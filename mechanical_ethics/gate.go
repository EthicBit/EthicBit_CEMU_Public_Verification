package mechanical_ethics

import (
	"errors"
	"fmt"

	cemucrypto "github.com/ethicbit/cemu/assurance/crypto"
)

var ErrFailClosed = errors.New("mechanical ethics fail-closed")

// CanonicalLogger writes only non-sensitive events to canonical evidence.
type CanonicalLogger interface {
	LogFailure(reason string)
	LogSecretProtected(meta ProtectedSecretMeta)
}

// RuntimeStopper terminates or blocks runtime progression on fail-closed.
type RuntimeStopper interface {
	Stop(reason string) error
}

// ProtectedSecretMeta stores only metadata. Never store HybridSecret.
type ProtectedSecretMeta struct {
	Algorithm     string `json:"algorithm"`
	KeyID         string `json:"key_id"`
	CiphertextLen int    `json:"ciphertext_len"`
	PublicKeyLen  int    `json:"public_key_len"`
}

type Gate struct {
	logger    CanonicalLogger
	stopper   RuntimeStopper
	protectFn func() (*cemucrypto.EncryptedSecret, error)
}

// NewGate initializes the gate and enforces protection of runtime secrets.
// It returns an error (fail-closed) instead of panic.
func NewGate(logger CanonicalLogger, stopper RuntimeStopper) (*Gate, error) {
	g := &Gate{
		logger:    logger,
		stopper:   stopper,
		protectFn: cemucrypto.HybridMLKEM768KeyEncapsulation,
	}

	if err := g.ProtectRuntimeSecrets(); err != nil {
		return nil, err
	}

	return g, nil
}

// ProtectRuntimeSecrets initializes the hybrid protection primitive and records
// only non-sensitive metadata in canonical artifacts.
func (g *Gate) ProtectRuntimeSecrets() error {
	secret, err := g.protectFn()
	if err != nil {
		return g.FailClosed("ml-kem768 hybrid encapsulation failed")
	}

	return g.RegisterProtectedSecret(secret)
}

// FailClosed is the single path to block progression on critical failures.
func (g *Gate) FailClosed(reason string) error {
	if g.logger != nil {
		g.logger.LogFailure(reason)
	}
	if g.stopper != nil {
		_ = g.stopper.Stop(reason)
	}
	return fmt.Errorf("%w: %s", ErrFailClosed, reason)
}

// RegisterProtectedSecret persists only metadata safe for canonical evidence.
func (g *Gate) RegisterProtectedSecret(secret *cemucrypto.EncryptedSecret) error {
	if secret == nil {
		return g.FailClosed("nil protected secret")
	}
	if len(secret.Ciphertext) == 0 || len(secret.PublicKey) == 0 || secret.KeyID == "" {
		return g.FailClosed("invalid protected secret metadata")
	}

	meta := ProtectedSecretMeta{
		Algorithm:     secret.Algorithm,
		KeyID:         secret.KeyID,
		CiphertextLen: len(secret.Ciphertext),
		PublicKeyLen:  len(secret.PublicKey),
	}

	if g.logger != nil {
		g.logger.LogSecretProtected(meta)
	}

	// Explicitly avoid any persistence of secret.HybridSecret.
	return nil
}
