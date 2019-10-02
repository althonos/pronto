#!/bin/sh

# --- Update GitHub release notes --------------------------------------------

export GEM_PATH="$(ruby -r rubygems -e 'puts Gem.user_dir')"
export PATH="${GEM_PATH}/bin:$PATH"

echo ">>> Installing chandler gem"
gem install --user-install 'faraday:<0.16' chandler

echo ">>> Updating GitHub release notes"
chandler push --github="$TRAVIS_REPO_SLUG" --changelog="CHANGELOG.md"
