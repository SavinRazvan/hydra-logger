## 📝 Description

Brief description of changes made in this pull request.

## 🎯 Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test addition or improvement

## 🔗 Related Issue

Closes #[issue_number]

## 🧪 Testing

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Examples updated if needed
- [ ] Manual testing completed

### Test Commands
```bash
# Run all tests
python -m pytest -q

# Run with coverage
python -m pytest --cov=hydra_logger --cov-report=term-missing -q

# Run examples
python examples/run_all_examples.py
```

## 📋 Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated (README, docstrings, etc.)
- [ ] CHANGELOG.md updated for significant changes
- [ ] No new warnings or errors introduced
- [ ] All CI checks pass

### Module Documentation Completion (required when `hydra_logger/**` changes)

- [ ] Affected module pages in `docs/modules/` were reviewed and updated.
- [ ] `docs/modules/README.md` index updated if module boundaries changed.
- [ ] `docs/MODULE_DOCS_AUDIT.md` findings and coverage matrix refreshed.
- [ ] Mermaid workflow diagrams updated for changed runtime flows.
- [ ] Links from `README.md` and `docs/ARCHITECTURE.md` to module docs were validated.

## 📊 Impact Assessment

- **Breaking Changes**: [ ] Yes [ ] No
  - If yes, describe the changes and migration path
- **Performance Impact**: [ ] None [ ] Minor [ ] Significant
- **Dependencies**: [ ] No new dependencies [ ] New dependencies added
- **Documentation**: [ ] No updates needed [ ] Updates included

## 🔍 Code Review Notes

Any specific areas you'd like reviewers to focus on or questions you have.

## 📸 Screenshots (if applicable)

If this PR includes UI changes, please include screenshots.

## 📚 Additional Context

Any additional context or information that might be helpful for reviewers. 