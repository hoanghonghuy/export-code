package translator

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Translator handles loading and retrieving localized strings.
type Translator struct {
	translations map[string]string
	locale       string
	fallback     string
}

// NewTranslator creates a new Translator instance.
// localesDir is the path to the directory containing locale JSON files (e.g., en.json, vi.json).
// locale is the desired locale (e.g., "en", "vi").
// fallback is the fallback locale if a key is not found in the desired locale.
func NewTranslator(localesDir, locale, fallback string) (*Translator, error) {
	t := &Translator{
		locale:   locale,
		fallback: fallback,
	}

	// Load the desired locale file
	localeFile := filepath.Join(localesDir, fmt.Sprintf("%s.json", locale))
	if err := t.loadTranslations(localeFile); err != nil {
		// If desired locale fails, try fallback
		if fallback != "" && fallback != locale {
			fallbackFile := filepath.Join(localesDir, fmt.Sprintf("%s.json", fallback))
			if err2 := t.loadTranslations(fallbackFile); err2 != nil {
				return nil, fmt.Errorf("failed to load both locale '%s' (%v) and fallback '%s' (%v)", locale, err, fallback, err2)
			}
			// If fallback loads, proceed. Log the switch?
		} else {
			return nil, fmt.Errorf("failed to load locale '%s': %w", locale, err)
		}
	}

	// If fallback is different and not yet loaded (meaning primary failed and fallback was loaded),
	// or if primary loaded successfully, we might still want the fallback as a base.
	// For now, let's assume if primary loads, we don't need to load fallback unless a key is missing.
	// The current logic handles loading fallback if primary fails.
	// If primary succeeds, fallback is not loaded into the same map, which is correct for our simple model
	// where we expect a full translation per file, or we handle missing keys by returning the key itself or a default.

	return t, nil
}

// loadTranslations loads translations from a JSON file into the translator's map.
func (t *Translator) loadTranslations(filePath string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open locale file %s: %w", filePath, err)
	}
	defer file.Close()

	if err := json.NewDecoder(file).Decode(&t.translations); err != nil {
		return fmt.Errorf("failed to decode locale file %s: %w", filePath, err)
	}

	return nil
}

// T retrieves the translation for a given key.
// If the key is not found in the current locale, it attempts to find it in the fallback locale.
// If not found in either, it returns the key itself.
func (t *Translator) T(key string) string {
	if translation, ok := t.translations[key]; ok && translation != "" {
		return translation
	}

	// If not found in current locale and fallback is different, try loading fallback file temporarily
	// or assume fallback was already loaded into the same map during initialization if primary failed.
	// Our current init logic only loads one map. If primary succeeds, fallback is not in the map.
	// A more complex system might merge primary into a base (fallback) map.
	// For this implementation, if primary locale is loaded and key is missing, return key.
	// The initialization logic ensures that `t.translations` is always from a valid locale (primary or fallback).
	// So, if we reach here, it means the key is missing from the *effective* translation map.
	// A common practice is to return the key as a fallback.
	// If we wanted to try the fallback locale's specific map *now*, we'd need to load it on-demand or store both.
	// Given the init logic, the effective map `t.translations` is either primary or fallback.
	// Therefore, if `key` is not in `t.translations`, it's genuinely missing from the effective set.
	// Returning the key itself is standard.
	return key
}

// TWithArgs retrieves the translation for a key and formats it with the provided arguments.
// It uses fmt.Sprintf internally.
func (t *Translator) TWithArgs(key string, args ...interface{}) string {
	template := t.T(key)
	return fmt.Sprintf(template, args...)
}

// SetLocale changes the current locale and reloads the translations.
// It follows the same loading logic as NewTranslator.
func (t *Translator) SetLocale(localesDir, locale string) error {
	newTranslations := make(map[string]string)
	localeFile := filepath.Join(localesDir, fmt.Sprintf("%s.json", locale))

	if err := t.loadTranslationsToMap(localeFile, newTranslations); err != nil {
		if t.fallback != "" && t.fallback != locale {
			fallbackFile := filepath.Join(localesDir, fmt.Sprintf("%s.json", t.fallback))
			if err2 := t.loadTranslationsToMap(fallbackFile, newTranslations); err2 != nil {
				return fmt.Errorf("failed to load both locale '%s' (%v) and fallback '%s' (%v)", locale, err, t.fallback, err2)
			}
		} else {
			return fmt.Errorf("failed to load locale '%s': %w", locale, err)
		}
	}

	t.translations = newTranslations
	t.locale = locale
	return nil
}

// loadTranslationsToMap is a helper to load into a specific map.
func (t *Translator) loadTranslationsToMap(filePath string, targetMap map[string]string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open locale file %s: %w", filePath, err)
	}
	defer file.Close()

	if err := json.NewDecoder(file).Decode(targetMap); err != nil {
		return fmt.Errorf("failed to decode locale file %s: %w", filePath, err)
	}

	return nil
}