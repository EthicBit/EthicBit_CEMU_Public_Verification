package mechanical_ethics

import (
	"errors"
	"testing"

	cemucrypto "github.com/ethicbit/cemu/assurance/crypto"
)

type testLogger struct {
	failures []string
	records  []ProtectedSecretMeta
}

func (l *testLogger) LogFailure(reason string) {
	l.failures = append(l.failures, reason)
}

func (l *testLogger) LogSecretProtected(meta ProtectedSecretMeta) {
	l.records = append(l.records, meta)
}

type testStopper struct {
	reasons []string
}

func (s *testStopper) Stop(reason string) error {
	s.reasons = append(s.reasons, reason)
	return nil
}

type successProtector struct{}

func (p successProtector) Protect() (*cemucrypto.EncryptedSecret, error) {
	return &cemucrypto.EncryptedSecret{
		Algorithm:  "HYBRID_ML-KEM768_X25519",
		Ciphertext: []byte{0x01, 0x02, 0x03},
		KeyID:      "ETHICBIT_TEST_KEY",
		PublicKey:  []byte{0xAA, 0xBB},
	}, nil
}

func (p successProtector) Name() string {
	return "test-success-protector"
}

type failingProtector struct{}

func (p failingProtector) Protect() (*cemucrypto.EncryptedSecret, error) {
	return nil, errors.New("protector failure")
}

func (p failingProtector) Name() string {
	return "test-failing-protector"
}

func TestNewGateWithProtectorSuccess(t *testing.T) {
	logger := &testLogger{}
	stopper := &testStopper{}

	g, err := NewGateWithProtector(successProtector{}, logger, stopper)
	if err != nil {
		t.Fatalf("expected gate init success, got err=%v", err)
	}
	if g == nil {
		t.Fatalf("expected non-nil gate")
	}
	if len(logger.failures) != 0 {
		t.Fatalf("expected no logged failures, got %d", len(logger.failures))
	}
	if len(stopper.reasons) != 0 {
		t.Fatalf("expected no stop calls, got %d", len(stopper.reasons))
	}
	if len(logger.records) != 1 {
		t.Fatalf("expected 1 protected-secret metadata record, got %d", len(logger.records))
	}
	record := logger.records[0]
	if record.KeyID != "ETHICBIT_TEST_KEY" {
		t.Fatalf("unexpected key id: %s", record.KeyID)
	}
	if record.Protector != "test-success-protector" {
		t.Fatalf("unexpected protector name: %s", record.Protector)
	}
}

func TestNewGateWithProtectorNilProtectorFailClosed(t *testing.T) {
	logger := &testLogger{}
	stopper := &testStopper{}

	_, err := NewGateWithProtector(nil, logger, stopper)
	if err == nil {
		t.Fatalf("expected fail-closed error for nil protector")
	}
	if !errors.Is(err, ErrFailClosed) {
		t.Fatalf("expected ErrFailClosed, got %v", err)
	}
	if len(logger.failures) != 1 {
		t.Fatalf("expected one logged failure, got %d", len(logger.failures))
	}
	if len(stopper.reasons) != 1 {
		t.Fatalf("expected one stop call, got %d", len(stopper.reasons))
	}
}

func TestNewGateWithProtectorProtectErrorFailClosed(t *testing.T) {
	logger := &testLogger{}
	stopper := &testStopper{}

	_, err := NewGateWithProtector(failingProtector{}, logger, stopper)
	if err == nil {
		t.Fatalf("expected fail-closed error for protector failure")
	}
	if !errors.Is(err, ErrFailClosed) {
		t.Fatalf("expected ErrFailClosed, got %v", err)
	}
	if len(logger.failures) != 1 {
		t.Fatalf("expected one logged failure, got %d", len(logger.failures))
	}
	if len(stopper.reasons) != 1 {
		t.Fatalf("expected one stop call, got %d", len(stopper.reasons))
	}
}

func TestNewGateUsesDefaultProtector(t *testing.T) {
	previous := newDefaultRuntimeSecretProtector
	t.Cleanup(func() {
		newDefaultRuntimeSecretProtector = previous
	})
	newDefaultRuntimeSecretProtector = func() RuntimeSecretProtector {
		return successProtector{}
	}

	g, err := NewGate(nil, nil)
	if err != nil {
		t.Fatalf("expected NewGate success with injected default protector, got err=%v", err)
	}
	if g == nil {
		t.Fatalf("expected non-nil gate")
	}
}
