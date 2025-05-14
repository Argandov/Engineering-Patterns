package helpers

import (
	"bytes"
	"fmt"
	"os/exec"
)

// Run executes name with args, returning an error that includes output.
func Run(name string, args ...string) error {
	cmd := exec.Command(name, args...)

	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("%s %v failed: %w – output: %s", name, args, err, out)
	}
	return nil
}

// PipeInput runs name with args, piping input into its stdin.
func PipeInput(input, name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Stdin = bytes.NewBufferString(input)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("%s %v failed: %w – output: %s", name, args, err, out)
	}
	return nil
}
