
#ifndef ASCON_H
#define ASCON_H

#include <stdint.h>
#include <stddef.h>
#include <string.h>

// ── Tailles standard ASCON-AEAD128 ─────────────────────────────────────────
#define ASCON_KEY_LEN    16
#define ASCON_NONCE_LEN  16
#define ASCON_TAG_LEN    16

// ── Rotation 64-bit droite ──────────────────────────────────────────────────
static inline uint64_t rotr64(uint64_t x, int n) {
    return (x >> n) | (x << (64 - n));
}

// ── Big-Endian load/store 64-bit ────────────────────────────────────────────
static inline uint64_t load64be(const uint8_t* b) {
    return ((uint64_t)b[0] << 56) | ((uint64_t)b[1] << 48) |
           ((uint64_t)b[2] << 40) | ((uint64_t)b[3] << 32) |
           ((uint64_t)b[4] << 24) | ((uint64_t)b[5] << 16) |
           ((uint64_t)b[6] <<  8) | ((uint64_t)b[7]);
}

static inline void store64be(uint8_t* b, uint64_t v) {
    b[0] = (uint8_t)(v >> 56); b[1] = (uint8_t)(v >> 48);
    b[2] = (uint8_t)(v >> 40); b[3] = (uint8_t)(v >> 32);
    b[4] = (uint8_t)(v >> 24); b[5] = (uint8_t)(v >> 16);
    b[6] = (uint8_t)(v >>  8); b[7] = (uint8_t)(v);
}

// ── État ASCON : 5 mots de 64 bits ──────────────────────────────────────────
typedef struct { uint64_t x[5]; } AsconState;

// ── Permutation ASCON ───────────────────────────────────────────────────────
static void ascon_permutation(AsconState* S, int rounds) {
    for (int r = 12 - rounds; r < 12; r++) {
        // Constante de ronde
        S->x[2] ^= (uint64_t)(0xf0 - r * 0x10 + r * 0x01);

        // Couche substitution
        S->x[0] ^= S->x[4];
        S->x[4] ^= S->x[3];
        S->x[2] ^= S->x[1];
        uint64_t T[5];
        T[0] = (~S->x[0]) & S->x[1];
        T[1] = (~S->x[1]) & S->x[2];
        T[2] = (~S->x[2]) & S->x[3];
        T[3] = (~S->x[3]) & S->x[4];
        T[4] = (~S->x[4]) & S->x[0];
        S->x[0] ^= T[1];
        S->x[1] ^= T[2];
        S->x[2] ^= T[3];
        S->x[3] ^= T[4];
        S->x[4] ^= T[0];
        S->x[1] ^= S->x[0];
        S->x[0] ^= S->x[4];
        S->x[3] ^= S->x[2];
        S->x[2] ^= (uint64_t)0xFFFFFFFFFFFFFFFFULL;

        // Couche diffusion linéaire
        S->x[0] ^= rotr64(S->x[0], 19) ^ rotr64(S->x[0], 28);
        S->x[1] ^= rotr64(S->x[1], 61) ^ rotr64(S->x[1], 39);
        S->x[2] ^= rotr64(S->x[2],  1) ^ rotr64(S->x[2],  6);
        S->x[3] ^= rotr64(S->x[3], 10) ^ rotr64(S->x[3], 17);
        S->x[4] ^= rotr64(S->x[4],  7) ^ rotr64(S->x[4], 41);
    }
}

// ── Initialisation ASCON-AEAD128 ────────────────────────────────────────────
// IV Python : [version=1, 0, (b<<4)+a=0x8C, 0x00, 0x80, rate=0x10, 0, 0]
// = 0x01008C008010 0000
static void ascon_initialize(AsconState* S,
                              const uint8_t key[16],
                              const uint8_t nonce[16])
{
 
    uint64_t iv_word = ((uint64_t)0x01 << 56) |
                       ((uint64_t)0x00 << 48) |
                       ((uint64_t)0x8C << 40) |
                       ((uint64_t)0x00 << 32) |
                       ((uint64_t)0x80 << 24) |
                       ((uint64_t)0x10 << 16) |
                       ((uint64_t)0x00 <<  8) |
                       ((uint64_t)0x00);

    S->x[0] = iv_word;
    S->x[1] = load64be(key);
    S->x[2] = load64be(key + 8);
    S->x[3] = load64be(nonce);
    S->x[4] = load64be(nonce + 8);

    ascon_permutation(S, 12);

 
    S->x[3] ^= load64be(key);
    S->x[4] ^= load64be(key + 8);
}

// ── Traitement des données associées ────────────────────────────────────────
static void ascon_process_ad(AsconState* S,
                              const uint8_t* ad, size_t adlen)
{
    if (adlen == 0) {
        S->x[4] ^= (uint64_t)1 << 63;
        return;
    }

    // Padding : AD || 0x01 || 0x00...
    // Traiter par blocs de 16 bytes
    size_t rate = 16;
    size_t blocks = (adlen / rate) + 1;  

    for (size_t blk = 0; blk < blocks; blk++) {
        size_t offset = blk * rate;
        uint8_t buf[16] = {0};

        if (offset + rate <= adlen) {
            // Bloc complet
            S->x[0] ^= load64be(ad + offset);
            S->x[1] ^= load64be(ad + offset + 8);
        } else {
            // Dernier bloc partiel : copier ce qui reste + padding 0x01
            size_t rem = adlen - offset;
            memcpy(buf, ad + offset, rem);
            buf[rem] = 0x01;
            S->x[0] ^= load64be(buf);
            S->x[1] ^= load64be(buf + 8);
        }
        ascon_permutation(S, 8);
    }

    S->x[4] ^= (uint64_t)1 << 63;
}

// ── Chiffrement ASCON-AEAD128 ───────────────────────────────────────────────
// Entrée  : key[16], nonce[16], ad[adlen], plaintext[ptlen]
// Sortie  : ciphertext[ptlen + 16]  (texte chiffré + tag)
static void ascon_aead_encrypt(const uint8_t key[16],
                                const uint8_t nonce[16],
                                const uint8_t* ad, size_t adlen,
                                const uint8_t* plaintext, size_t ptlen,
                                uint8_t* ciphertext)
{
    AsconState S;
    size_t rate = 16;

    // 1. Initialisation
    ascon_initialize(&S, key, nonce);

    // 2. Données associées
    ascon_process_ad(&S, ad, adlen);

    // 3. Chiffrement du plaintext
    size_t p_lastlen = ptlen % rate;
    size_t full_blocks = ptlen / rate;

    // Blocs complets
    for (size_t blk = 0; blk < full_blocks; blk++) {
        size_t off = blk * rate;
        S.x[0] ^= load64be(plaintext + off);
        S.x[1] ^= load64be(plaintext + off + 8);
        store64be(ciphertext + off,     S.x[0]);
        store64be(ciphertext + off + 8, S.x[1]);
        ascon_permutation(&S, 8);
    }

    // Dernier bloc (partiel) avec padding
    {
        size_t off = full_blocks * rate;
        uint8_t buf[16] = {0};
        memcpy(buf, plaintext + off, p_lastlen);
        buf[p_lastlen] = 0x01;  // padding

        S.x[0] ^= load64be(buf);
        S.x[1] ^= load64be(buf + 8);

        // N'écrire que p_lastlen bytes de ciphertext
        uint8_t out0[8], out1[8];
        store64be(out0, S.x[0]);
        store64be(out1, S.x[1]);
        size_t take0 = (p_lastlen < 8) ? p_lastlen : 8;
        size_t take1 = (p_lastlen > 8) ? (p_lastlen - 8) : 0;
        memcpy(ciphertext + off,     out0, take0);
        memcpy(ciphertext + off + 8, out1, take1);
    }

 
    S.x[2] ^= load64be(key);
    S.x[3] ^= load64be(key + 8);

    ascon_permutation(&S, 12);

    // S[3] ^= key[-16:-8],  S[4] ^= key[-8:]
    S.x[3] ^= load64be(key);
    S.x[4] ^= load64be(key + 8);

    // Tag = S[3] || S[4]
    store64be(ciphertext + ptlen,     S.x[3]);
    store64be(ciphertext + ptlen + 8, S.x[4]);
}

// ── Déchiffrement ASCON-AEAD128 ─────────────────────────────────────────────
// Entrée  : key[16], nonce[16], ad[adlen], ciphertext[ctlen] (ctlen >= 16)
// Sortie  : plaintext[ctlen-16], retourne 0 si OK, -1 si tag invalide
static int ascon_aead_decrypt(const uint8_t key[16],
                               const uint8_t nonce[16],
                               const uint8_t* ad, size_t adlen,
                               const uint8_t* ciphertext, size_t ctlen,
                               uint8_t* plaintext)
{
    if (ctlen < ASCON_TAG_LEN) return -1;
    size_t ptlen = ctlen - ASCON_TAG_LEN;
    size_t rate  = 16;

    AsconState S;
    ascon_initialize(&S, key, nonce);
    ascon_process_ad(&S, ad, adlen);

    size_t c_lastlen = ptlen % rate;
    size_t full_blocks = ptlen / rate;

    for (size_t blk = 0; blk < full_blocks; blk++) {
        size_t off = blk * rate;
        uint64_t c0 = load64be(ciphertext + off);
        uint64_t c1 = load64be(ciphertext + off + 8);
        store64be(plaintext + off,     S.x[0] ^ c0);
        store64be(plaintext + off + 8, S.x[1] ^ c1);
        S.x[0] = c0;
        S.x[1] = c1;
        ascon_permutation(&S, 8);
    }

    {
        size_t off = full_blocks * rate;
        uint8_t c_pad[16]  = {0};
        uint8_t c_mask[16];
        memset(c_mask, 0xFF, sizeof(c_mask));

    
        uint8_t c_padx[16] = {0};
        c_padx[c_lastlen] = 0x01;
   
        memset(c_mask, 0x00, c_lastlen);
  
        memset(c_mask, 0x00, 16);
        memset(c_mask + c_lastlen, 0xFF, rate - c_lastlen);

        memcpy(c_pad, ciphertext + off, c_lastlen);

        uint64_t Ci0 = load64be(c_pad);
        uint64_t Ci1 = load64be(c_pad + 8);

        // plaintext derniers octets
        uint8_t pt_full[16];
        store64be(pt_full,     S.x[0] ^ Ci0);
        store64be(pt_full + 8, S.x[1] ^ Ci1);
        memcpy(plaintext + off, pt_full, c_lastlen);

        // Mise à jour état
        uint64_t mask0 = load64be(c_mask);
        uint64_t mask1 = load64be(c_mask + 8);
        uint64_t padx0 = load64be(c_padx);
        uint64_t padx1 = load64be(c_padx + 8);
        S.x[0] = (S.x[0] & mask0) ^ Ci0 ^ padx0;
        S.x[1] = (S.x[1] & mask1) ^ Ci1 ^ padx1;
    }

    // Finalisation
    S.x[2] ^= load64be(key);
    S.x[3] ^= load64be(key + 8);
    ascon_permutation(&S, 12);
    S.x[3] ^= load64be(key);
    S.x[4] ^= load64be(key + 8);

    // Vérification tag
    uint8_t tag_calc[16];
    store64be(tag_calc,     S.x[3]);
    store64be(tag_calc + 8, S.x[4]);

    const uint8_t* tag_recv = ciphertext + ptlen;
    int ok = (memcmp(tag_calc, tag_recv, 16) == 0) ? 0 : -1;
    return ok;
}

#endif // ASCON_H