# Badge Automation

This document explains how the badge automation system works in Hydra-Logger and how to use it.

## Overview

The badge automation system automatically updates the README.md badges with current test and coverage statistics. This ensures that the badges always reflect the actual state of the project.

## How It Works

### Manual Usage

You can manually update the badges using the `scripts/update_badges.py` script:

```bash
# Update badges with current stats
python scripts/update_badges.py

# Preview changes without making them
python scripts/update_badges.py --dry-run

# Specify a custom README path
python scripts/update_badges.py --readme-path path/to/README.md

# Override stats (useful for CI/CD)
python scripts/update_badges.py --test-count 150 --coverage-percentage 98.5
```

### Automated Updates

The badges are automatically updated via GitHub Actions when:

1. Code is pushed to the `main` branch
2. Tests pass successfully
3. Coverage is calculated

The automation workflow:
1. Runs tests and calculates coverage
2. Extracts test count and coverage percentage
3. Updates the README.md badges
4. Commits and pushes the changes

## Badge Types

### Test Badge
- **Format**: `[![Tests](https://img.shields.io/badge/tests-{count}%20passed-darkgreen.svg)](https://github.com/SavinRazvan/hydra-logger)`
- **Shows**: Number of tests that pass
- **Color**: Dark green for passing tests

### Coverage Badge
- **Format**: `[![Coverage](https://img.shields.io/badge/coverage-{percentage}%25-darkgreen.svg)](https://github.com/SavinRazvan/hydra-logger)`
- **Shows**: Code coverage percentage
- **Color**: Dark green for good coverage

## Configuration

### CI/CD Integration

The badge automation is integrated into the GitHub Actions workflow in `.github/workflows/ci.yml`:

```yaml
update-badges:
  runs-on: ubuntu-latest
  needs: [test]
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  
  steps:
  - uses: actions/checkout@v4
    with:
      token: ${{ secrets.GITHUB_TOKEN }}
  
  - name: Set up Python
    uses: actions/setup-python@v4
    with:
      python-version: 3.12
  
  - name: Install dependencies
    run: |
      python -m pip install --upgrade pip
      pip install -e ".[dev]"
  
  - name: Get test count and coverage
    id: stats
    run: |
      # Get test count
      TEST_COUNT=$(python -m pytest --collect-only -q | tail -1 | grep -o '[0-9]*' | head -1)
      echo "test_count=$TEST_COUNT" >> $GITHUB_OUTPUT
      
      # Get coverage percentage
      COVERAGE_PCT=$(python -m pytest --cov=hydra_logger --cov-report=term-missing -q | grep 'TOTAL' | grep -o '[0-9]*%' | head -1 | sed 's/%//')
      echo "coverage_pct=$COVERAGE_PCT" >> $GITHUB_OUTPUT
      
      echo "📊 Stats: $TEST_COUNT tests, ${COVERAGE_PCT}% coverage"
  
  - name: Update README badges
    run: |
      python scripts/update_badges.py \
        --test-count ${{ steps.stats.outputs.test_count }} \
        --coverage-percentage ${{ steps.stats.outputs.coverage_pct }}
  
  - name: Commit and push changes
    run: |
      git config --local user.email "action@github.com"
      git config --local user.name "GitHub Action"
      git add README.md
      git diff --quiet && git diff --staged --quiet || git commit -m "🤖 Auto-update badges: ${{ steps.stats.outputs.test_count }} tests, ${{ steps.stats.outputs.coverage_pct }}% coverage"
      git push
```

### Script Configuration

The `scripts/update_badges.py` script supports several options:

- `--dry-run`: Show what would be changed without making changes
- `--readme-path`: Specify a custom path to the README file
- `--test-count`: Override the test count (useful for CI)
- `--coverage-percentage`: Override the coverage percentage (useful for CI)

## Troubleshooting

### Common Issues

1. **Script fails to get test count**
   - Ensure pytest is installed: `pip install pytest`
   - Check that tests can be discovered: `python -m pytest --collect-only`

2. **Script fails to get coverage**
   - Ensure pytest-cov is installed: `pip install pytest-cov`
   - Check that coverage can be generated: `python -m pytest --cov=hydra_logger`

3. **Badges not updating in CI**
   - Check that the workflow has write permissions
   - Verify that the push is to the main branch
   - Check the workflow logs for errors

### Manual Override

If the automation fails, you can manually update the badges:

```bash
# Get current stats
TEST_COUNT=$(python -m pytest --collect-only -q | tail -1 | grep -o '[0-9]*' | head -1)
COVERAGE_PCT=$(python -m pytest --cov=hydra_logger --cov-report=term-missing -q | grep 'TOTAL' | grep -o '[0-9]*%' | head -1 | sed 's/%//')

# Update badges
python scripts/update_badges.py --test-count $TEST_COUNT --coverage-percentage $COVERAGE_PCT
```

## Best Practices

1. **Always test changes**: Use `--dry-run` to preview changes
2. **Keep badges accurate**: Don't manually edit badge URLs
3. **Monitor CI**: Check that badge updates are working in CI
4. **Document changes**: Update this document when making changes to the automation

## Future Enhancements

Potential improvements to the badge automation system:

1. **Dynamic badges**: Use shields.io dynamic badges that update automatically
2. **More metrics**: Add badges for code quality, security, etc.
3. **Custom thresholds**: Configure minimum coverage/test thresholds
4. **Multiple formats**: Support different badge styles and colors
5. **Integration**: Integrate with external services like Codecov, SonarCloud, etc.

## Related Files

- `scripts/update_badges.py` - Main automation script
- `.github/workflows/ci.yml` - CI/CD workflow with badge updates
- `README.md` - Contains the badges that get updated
- `pyproject.toml` - Test and coverage configuration 