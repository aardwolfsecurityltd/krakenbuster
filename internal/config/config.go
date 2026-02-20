package config

import (
	"fmt"
	"os"
	"path/filepath"

	"gopkg.in/ini.v1"
)

// Config holds all persistent configuration values.
type Config struct {
	Threads   int    `ini:"threads"`
	Rate      int    `ini:"rate"`
	Proxy     string `ini:"proxy"`
	OutputDir string `ini:"output_dir"`
}

// DefaultConfig returns a Config populated with sensible defaults.
func DefaultConfig() *Config {
	return &Config{
		Threads:   50,
		Rate:      200,
		Proxy:     "",
		OutputDir: "./output",
	}
}

// configPath returns the full path to ~/.krakenbuster.conf.
func configPath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("locating home directory: %w", err)
	}
	return filepath.Join(home, ".krakenbuster.conf"), nil
}

// Load reads the configuration file, creating it with defaults if it does not
// exist. Values from the file override the defaults.
func Load() (*Config, error) {
	cfg := DefaultConfig()

	path, err := configPath()
	if err != nil {
		return cfg, fmt.Errorf("resolving config path: %w", err)
	}

	if _, err := os.Stat(path); os.IsNotExist(err) {
		if saveErr := Save(cfg); saveErr != nil {
			return cfg, fmt.Errorf("creating default config: %w", saveErr)
		}
		return cfg, nil
	}

	iniFile, err := ini.Load(path)
	if err != nil {
		return cfg, fmt.Errorf("reading config file %s: %w", path, err)
	}

	if err := iniFile.Section("").MapTo(cfg); err != nil {
		return cfg, fmt.Errorf("parsing config file %s: %w", path, err)
	}

	return cfg, nil
}

// Save writes the current configuration to ~/.krakenbuster.conf.
func Save(cfg *Config) error {
	path, err := configPath()
	if err != nil {
		return fmt.Errorf("resolving config path: %w", err)
	}

	iniFile := ini.Empty()
	if err := iniFile.Section("").ReflectFrom(cfg); err != nil {
		return fmt.Errorf("serialising config: %w", err)
	}

	if err := iniFile.SaveTo(path); err != nil {
		return fmt.Errorf("writing config file %s: %w", path, err)
	}

	return nil
}
