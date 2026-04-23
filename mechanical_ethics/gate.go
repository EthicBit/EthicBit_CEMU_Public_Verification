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

// RuntimeSecretProtector abstracts runtime secret protection primitives.
// Implementations must return only the encrypted material required by the gate.
type RuntimeSecretProtector interface {
	Protect() (*cemucrypto.EncryptedSecret, error)
	Name() string
}

// ProtectedSecretMeta stores only metadata. Never store HybridSecret.
type ProtectedSecretMeta struct {
	Algorithm     string `json:"algorithm"`
	KeyID         string `json:"key_id"`
	CiphertextLen int    `json:"ciphertext_len"`
	PublicKeyLen  int    `json:"public_key_len"`
	Protector     string `json:"protector,omitempty"`
}

type Gate struct {
	logger    CanonicalLogger
	stopper   RuntimeStopper
	protector RuntimeSecretProtector
}

type mlkem768Protector struct{}

func (p mlkem768Protector) Protect() (*cemucrypto.EncryptedSecret, error) {
	return cemucrypto.HybridMLKEM768KeyEncapsulation()
}

func (p mlkem768Protector) Name() string {
	return "MLKEM768Protector"
}

var newDefaultRuntimeSecretProtector = func() RuntimeSecretProtector {
	return mlkem768Protector{}
}

// NewGate initializes the gate with the default runtime secret protector and
// enforces protection of runtime secrets. It returns an error (fail-closed)
// instead of panic.
func NewGate(logger CanonicalLogger, stopper RuntimeStopper) (*Gate, error) {
	return NewGateWithProtector(newDefaultRuntimeSecretProtector(), logger, stopper)
}

// NewGateWithProtector initializes the gate with an explicit protector.
func NewGateWithProtector(protector RuntimeSecretProtector, logger CanonicalLogger, stopper RuntimeStopper) (*Gate, error) {
	g := &Gate{
		logger:    logger,
		stopper:   stopper,
		protector: protector,
	}

	if g.protector == nil {
		return nil, g.FailClosed("runtime secret protector not configured")
	}

	if err := g.ProtectRuntimeSecrets(); err != nil {
		return nil, err
	}

	return g, nil
}

// ProtectRuntimeSecrets initializes the hybrid protection primitive and records
// only non-sensitive metadata in canonical artifacts.
func (g *Gate) ProtectRuntimeSecrets() error {
	secret, err := g.protector.Protect()
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

	protectorName := "unknown"
	if g.protector != nil {
		protectorName = g.protector.Name()
	}

	meta := ProtectedSecretMeta{
		Algorithm:     secret.Algorithm,
		KeyID:         secret.KeyID,
		CiphertextLen: len(secret.Ciphertext),
		PublicKeyLen:  len(secret.PublicKey),
		Protector:     protectorName,
	}

	if g.logger != nil {
		g.logger.LogSecretProtected(meta)
	}

	// Explicitly avoid any persistence of secret.HybridSecret.
	return nil
}
