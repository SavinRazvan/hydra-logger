## Summary

- (describe what changed and why)

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test addition or improvement

## Related Issue

Closes #[issue_number]

## Test plan

- [ ] All existing tests pass (`python -m pytest -q`)
- [ ] New tests added for new functionality
- [ ] Slim-header check passes (`python scripts/pr/check_slim_headers.py --all-python --strict`)
- [ ] Examples updated if needed
- [ ] Manual testing completed

## Checklist

- [ ] Self-review of code completed
- [ ] Documentation updated (README, docstrings, module docs)
- [ ] No new warnings or errors introduced
- [ ] All CI checks pass

### Module Documentation (required when `hydra_logger/**` changes)

- [ ] Affected module pages in `docs/modules/` reviewed and updated
- [ ] `docs/modules/README.md` index updated if module boundaries changed
- [ ] `docs/MODULE_DOCS_AUDIT.md` findings and coverage matrix refreshed
- [ ] Mermaid workflow diagrams updated for changed runtime flows
- [ ] Links from `README.md` and `docs/ARCHITECTURE.md` validated

## Impact Assessment

- Breaking Changes: [ ] Yes [ ] No
- Performance Impact: [ ] None [ ] Minor [ ] Significant
- New Dependencies: [ ] No [ ] Yes

## Attribution

- Author: Savin I. Razvan
- GitHub-User: @SavinRazvan
- Agent/s: review-pr | prepare-pr | merge-pr
- Made-with: Cursor
