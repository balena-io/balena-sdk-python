'use strict';

const execSync = require('child_process').execSync;
const exec = require('child_process').exec;
const path = require('path');

const getAuthor = (commitHash) => {
  return execSync(`git show --quiet --format="%an" ${commitHash}`, {
    encoding: 'utf8'
  }).replace('\n', '');
};

const isIncrementalCommit = (changeType) => {
  return Boolean(changeType) && changeType.trim().toLowerCase() !== 'none';
};

module.exports = {
  // This setup allows the editing and parsing of footer tags to get version and type information,
  // as well as ensuring tags of the type 'v<major>.<minor>.<patch>' are used.
  // It increments in a semver compatible fashion and allows the updating of NPM package info.
  editChangelog: true,
  parseFooterTags: true,
  getGitReferenceFromVersion: 'v-prefix',
  incrementVersion: 'semver',
  updateVersion: (cwd, version, callback) => {
    execSync(`sed -i '/^__version__ = ".*"/  s/^__version__ = ".*"/__version__ = "${version}"/g' balena/__init__.py`, {encoding: 'utf8'});

    const pyprojectToml = path.join(cwd, 'pyproject.toml');
    return exec(`sed -i '/\[tool\.poetry\]/,/^version = ".*"/  s/^version = ".*"/version = "${version}"/g' ${pyprojectToml}`,
    {
      encoding: 'utf8',
    }, callback);
  },

  // Always add the entry to the top of the Changelog, below the header.
  addEntryToChangelog: {
    preset: 'prepend',
    fromLine: 6
  },

  // Only include a commit when there is a footer tag of 'change-type'.
  // Ensures commits which do not up versions are not included.
  includeCommitWhen: (commit) => {
    return isIncrementalCommit(commit.footer['change-type']);
  },

  // Determine the type from 'change-type:' tag.
  // Should no explicit change type be made, then no changes are assumed.

  getIncrementLevelFromCommit: (commit) => {
    const match = commit.subject.match(/^(patch|minor|major):/i);
    if (Array.isArray(match) && isIncrementalCommit(match[1])) {
      return match[1].trim().toLowerCase();
    }

    if (isIncrementalCommit(commit.footer['change-type'])) {
      return commit.footer['change-type'].trim().toLowerCase();
    }
  },

  // If a 'changelog-entry' tag is found, use this as the subject rather than the
  // first line of the commit.
  transformTemplateData: (data) => {
    data.commits.forEach((commit) => {
      commit.subject = commit.footer['changelog-entry'] || commit.subject;
      commit.author = getAuthor(commit.hash);
    });

    return data;
  },

  template: [
    '## v{{version}} - {{moment date "Y-MM-DD"}}',
    '',
    '{{#each commits}}',
    '{{#if this.author}}',
    '* {{capitalize this.subject}} [{{this.author}}]',
    '{{else}}',
    '* {{capitalize this.subject}}',
    '{{/if}}',
    '{{/each}}'
  ].join('\n')
};
