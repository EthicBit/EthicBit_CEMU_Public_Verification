package crypto

import (
	"encoding/json"
	"testing"
)

func TestHybridMLKEM768KeyEncapsulationProducesMetadataAndSecret(t *testing.T) {
	secret, err := HybridMLKEM768KeyEncapsulation()
	if err != nil {
		t.Fatalf("HybridMLKEM768KeyEncapsulation returned error: %v", err)
	}
	if secret == nil {
		t.Fatalf("expected non-nil secret")
	}
	if secret.Algorithm != "HYBRID_ML-KEM768_X25519" {
		t.Fatalf("unexpected algorithm: %s", secret.Algorithm)
	}
	if secret.KeyID != "ETHICBIT_MLKEM768_V1" {
		t.Fatalf("unexpected key id: %s", secret.KeyID)
	}
	if len(secret.Ciphertext) == 0 {
		t.Fatalf("expected ML-KEM ciphertext")
	}
	if len(secret.PublicKey) == 0 {
		t.Fatalf("expected X25519 public key")
	}
	if len(secret.PQPublicKey) == 0 {
		t.Fatalf("expected ML-KEM encapsulation public key")
	}
	if len(secret.HybridSecret) != 32 {
		t.Fatalf("expected 32-byte hybrid secret, got %d", len(secret.HybridSecret))
	}
}

func TestEncryptedSecretDoesNotSerializeHybridSecret(t *testing.T) {
	secret, err := HybridMLKEM768KeyEncapsulation()
	if err != nil {
		t.Fatalf("HybridMLKEM768KeyEncapsulation returned error: %v", err)
	}

	payload, err := json.Marshal(secret)
	if err != nil {
		t.Fatalf("json marshal returned error: %v", err)
	}

	var decoded map[string]json.RawMessage
	if err := json.Unmarshal(payload, &decoded); err != nil {
		t.Fatalf("json unmarshal returned error: %v", err)
	}
	if _, ok := decoded["HybridSecret"]; ok {
		t.Fatalf("HybridSecret must not be serialized with Go field name")
	}
	if _, ok := decoded["hybrid_secret"]; ok {
		t.Fatalf("hybrid_secret must not be serialized with JSON field name")
	}
	if _, ok := decoded["ciphertext"]; !ok {
		t.Fatalf("expected ciphertext metadata in JSON payload")
	}
	if _, ok := decoded["public_key"]; !ok {
		t.Fatalf("expected public_key metadata in JSON payload")
	}
	if _, ok := decoded["pq_public_key"]; !ok {
		t.Fatalf("expected pq_public_key metadata in JSON payload")
	}
}
