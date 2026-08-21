# Justfile for grahamdumpleton.me — run `just` to list available targets.

url := "http://localhost:8080"

# List available targets.
default:
    @just --list

# Install dependencies (run once on a new machine).
setup:
    npm install

# Build the static site into _site.
build:
    npm run build

# Start the development server with live reload and watch mode.
dev:
    npm run dev

# Start the development server without watch mode.
serve:
    npm run serve

# Open the local development site in the browser.
open:
    open {{url}}

# Remove the generated site output.
clean:
    rm -rf _site
