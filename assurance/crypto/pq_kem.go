package crypto

import (
	"bytes"
	"crypto/ecdh"
	"crypto/hkdf"
	"crypto/mlkem"
	"crypto/rand"
	"crypto/sha256"
	"errors"
)

// EncryptedSecret stores only non-sensitive fields for persistence.
// HybridSecret must never be serialized.
type EncryptedSecret struct {
	Algorithm    string `json:"algorithm"`
	Ciphertext   []byte `json:"ciphertext"`
	KeyID        string `json:"key_id"`
	PublicKey    []byte `json:"public_key"`
	PQPublicKey  []byte `json:"pq_public_key"`
	HybridSecret []byte `json:"-"`
}

// HybridMLKEM768KeyEncapsulation derives a runtime secret from:
// 1) ML-KEM768 shared secret and
// 2) X25519 ECDH shared secret.
func HybridMLKEM768KeyEncapsulation() (*EncryptedSecret, error) {
	// ML-KEM768 keypair (receiver) and encapsulation (sender).
	dk, err := mlkem.GenerateKey768()
	if err != nil {
		return nil, err
	}
	ek := dk.EncapsulationKey()

	sharedPQ, ciphertext := ek.Encapsulate()
	decSharedPQ, err := dk.Decapsulate(ciphertext)
	if err != nil {
		return nil, err
	}
	if !bytes.Equal(sharedPQ, decSharedPQ) {
		return nil, errors.New("ml-kem decapsulation mismatch")
	}

	// X25519 ECDH agreement between two ephemeral parties.
	curve := ecdh.X25519()
	privA, err := curve.GenerateKey(rand.Reader)
	if err != nil {
		return nil, err
	}
	privB, err := curve.GenerateKey(rand.Reader)
	if err != nil {
		return nil, err
	}
	sharedClassicA, err := privA.ECDH(privB.PublicKey())
	if err != nil {
		return nil, err
	}
	sharedClassicB, err := privB.ECDH(privA.PublicKey())
	if err != nil {
		return nil, err
	}
	if !bytes.Equal(sharedClassicA, sharedClassicB) {
		return nil, errors.New("x25519 shared-secret mismatch")
	}

	hybridSecret, err := hybridKDF(sharedPQ, sharedClassicA)
	if err != nil {
		return nil, err
	}

	return &EncryptedSecret{
		Algorithm:    "HYBRID_ML-KEM768_X25519",
		Ciphertext:   ciphertext,
		KeyID:        "ETHICBIT_MLKEM768_V1",
		PublicKey:    privB.PublicKey().Bytes(),
		PQPublicKey:  ek.Bytes(),
		HybridSecret: hybridSecret,
	}, nil
}

func hybridKDF(secretPQ, secretClassic []byte) ([]byte, error) {
	if len(secretPQ) == 0 || len(secretClassic) == 0 {
		return nil, errors.New("empty input secret")
	}

	// Hybrid extract material includes both secrets.
	ikm := make([]byte, 0, len(secretPQ)+len(secretClassic))
	ikm = append(ikm, secretPQ...)
	ikm = append(ikm, secretClassic...)

	salt := sha256.Sum256([]byte("ETHICBIT_HYBRID_MLKEM768_X25519_V1"))
	return hkdf.Key(sha256.New, ikm, salt[:], "mechanical-ethics-runtime-secret", 32)
}
