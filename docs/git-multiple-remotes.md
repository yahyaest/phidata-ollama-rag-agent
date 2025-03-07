# Managing Multiple Git Remote Repositories

This document explains how to handle two or more remote repositories for the same Git project. This is useful when you want to maintain copies of your code in different locations (e.g., a private company repository and a public GitHub repository).

## Current Repository Setup

This project currently has the following remote repository configured:

```bash
origin  https://git.macondo-engineering.com/ai-lab/phidata-ollama-rag-agent.git (fetch)
origin  https://git.macondo-engineering.com/ai-lab/phidata-ollama-rag-agent.git (push)
```

## Checking Existing Remotes

To view all configured remote repositories:

```bash
git remote -v
```

## Adding a Second Remote Repository

To add a GitHub repository as an additional remote:

```bash
git remote add github https://github.com/username/repository-name.git
```

Replace `github` with your preferred name for this remote and `username/repository-name` with your actual GitHub repository details.

## Pushing to a Specific Remote

### Push to the Original Remote (Macondo Engineering)

```bash
git push origin branch-name
```

### Push to the GitHub Remote

```bash
git push github branch-name
```

## Setting a Default Push Destination

To configure a specific branch to always push to a certain remote by default:

```bash
# Set GitHub as the default push destination for your current branch
git branch --set-upstream-to=github/branch-name

# Or set origin as the default
git branch --set-upstream-to=origin/branch-name
```

After setting this, you can simply use `git push` without specifying the remote.

## Pushing to All Remotes at Once

### Create a Git Alias

You can create an alias to push to all remotes:

```bash
git config alias.pushall '!git push origin && git push github'
```

Then use:

```bash
git pushall
```

### Alternative Method: Multiple Push URLs

You can configure a single remote to push to multiple repositories:

```bash
# Add GitHub as an additional push URL for the origin remote
git remote set-url --add --push origin https://github.com/username/repository-name.git
```

## Pulling From a Specific Remote

To pull from a specific remote:

```bash
git pull origin branch-name
git pull github branch-name
```

## Best Practices

1. **Consistent Branching Strategy**: Use the same branch names across all remotes to avoid confusion.
2. **Regular Synchronization**: Regularly push changes to all remotes to keep them in sync.
3. **Remote Naming Conventions**: Use meaningful names for your remotes that indicate where they point to.
4. **Documentation**: Document your remote setup for other team members.

## Common Issues and Solutions

### Different Commit History

If remotes have diverged significantly:

```bash
# Force push (use with caution!)
git push -f remote-name branch-name
```

### Merge Conflicts During Pull

Resolve conflicts locally:

```bash
git pull remote-name branch-name
# Resolve conflicts
git add .
git commit -m "Resolve merge conflicts"
git push
```

