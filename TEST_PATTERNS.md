# Test Patterns & Best Practices

## Overview
This guide documents the testing patterns used in the Marvel Champions backend and best practices for writing new tests.

---

## Test Structure

### Test File Organization
```
tests/
├── test_entities.py           # Entity validation tests
├── test_repositories.py       # Repository/database tests (mongomock)
├── test_interactors.py        # Business logic tests
├── test_interactors_advanced.py  # Advanced patterns and edge cases
└── test_api_integration.py    # API endpoint tests (TODO)
```

### Test Class Organization
```python
class TestCardInteractorAdvanced:
    """Test class for CardInteractor advanced features"""
    
    @pytest.fixture
    def card_interactor(self):
        """Setup fixture - creates fresh instance for each test"""
        mock_repo = Mock()
        mock_gateway = Mock()
        mock_storage = Mock()
        return CardInteractor(mock_repo, mock_gateway, mock_storage)
    
    def test_specific_feature(self, card_interactor):
        """Specific test - uses fixture via parameter"""
        pass
```

---

## Pattern 1: Mocking External Dependencies

### Problem
Interactors depend on repositories, gateways, and storage. We don't want real database calls during unit tests.

### Solution: Use `unittest.mock.Mock`

```python
def test_import_card_from_marvelcdb(self, card_interactor):
    """Test importing a card while mocking external dependencies"""
    
    # Setup mocks to return specific values
    card_interactor.card_repo.find_by_code = Mock(return_value=None)
    card_interactor.marvelcdb.get_card_info = Mock(return_value={
        'code': 'test_card',
        'name': 'Test Card',
        'text': 'Test text'
    })
    card_interactor.image_storage.image_exists = Mock(return_value=False)
    
    # Mock the save operation
    created_card = Card(code='test_card', name='Test Card', text='Test text')
    card_interactor.card_repo.save = Mock(return_value=created_card)
    
    # Patch the _download_card_image method since it's internal
    with patch.object(card_interactor, '_download_card_image'):
        result = card_interactor.import_card_from_marvelcdb('test_card')
    
    # Verify the result
    assert result is not None
    assert result.code == 'test_card'
    
    # Verify correct method calls
    card_interactor.card_repo.save.assert_called_once()
    card_interactor.marvelcdb.get_card_info.assert_called_once_with('test_card')
```

### Key Techniques
1. **Mock return values**: `Mock(return_value=...)`
2. **Side effects for sequences**: `Mock(side_effect=[value1, value2])`
3. **Assert calls were made**: `.assert_called_once()`, `.assert_called_with(...)`
4. **Patch internal methods**: `patch.object(obj, 'method_name')`

---

## Pattern 2: Testing Error Paths

### Problem
How do we test that errors are handled correctly?

### Solution: Use `pytest.raises` context manager

```python
def test_import_deck_no_cards(self, deck_interactor):
    """Test that importing a deck with no cards raises ValueError"""
    
    # Setup mocks to simulate error condition
    deck_interactor.marvelcdb.get_deck_cards = Mock(return_value=[])
    
    # Expect ValueError to be raised
    with pytest.raises(ValueError):
        deck_interactor.import_deck_from_marvelcdb('deck123')
    
    # The error should be raised before trying to save
    deck_interactor.deck_repo.save.assert_not_called()
```

### Common Patterns
```python
# Test for specific exception type
with pytest.raises(ValueError):
    some_function()

# Test for specific exception message
with pytest.raises(ValueError, match="Deck name cannot be empty"):
    some_function()

# Verify exception not raised
def test_something_succeeds():
    result = some_function()  # Should not raise
    assert result is not None
```

---

## Pattern 3: Testing State Transitions

### Problem
How do we verify complex multi-step operations?

### Solution: Chain mocks and verify intermediate states

```python
def test_create_deck_with_card_import(self, deck_interactor):
    """Test that creating a deck imports all required cards first"""
    
    card_codes = [('card1', 2), ('card2', 1)]
    
    # Mock the import step
    deck_interactor.card_interactor.import_cards_bulk = Mock()
    
    # Mock the save step
    created_deck = Deck(id='new_deck', name='My Deck', cards=())
    deck_interactor.deck_repo.save = Mock(return_value=created_deck)
    
    # Execute
    result = deck_interactor.create_deck('My Deck', card_codes)
    
    # Verify steps happened in correct order
    deck_interactor.card_interactor.import_cards_bulk.assert_called_once_with(['card1', 'card2'])
    deck_interactor.deck_repo.save.assert_called_once()
    
    # Verify result
    assert result.name == 'My Deck'
```

---

## Pattern 4: Testing Data Transformations

### Problem
How do we verify data is transformed correctly?

### Solution: Compare input and output

```python
def test_search_cards_by_name_returns_filtered_results(self, card_interactor):
    """Test that search returns only matching cards"""
    
    # Setup expected data
    all_cards = (
        Card(code='card1', name='Iron Man'),
        Card(code='card2', name='Iron Patriot'),
        Card(code='card3', name='Captain America')
    )
    expected_results = (all_cards[0], all_cards[1])  # Iron Man and Iron Patriot
    
    # Mock the repo to return filtered results
    card_interactor.card_repo.search_by_name = Mock(return_value=expected_results)
    
    # Execute
    result = card_interactor.search_cards('Iron')
    
    # Verify
    assert len(result) == 2
    assert all('Iron' in card.name for card in result)
    card_interactor.card_repo.search_by_name.assert_called_once_with('Iron')
```

---

## Pattern 5: Testing Edge Cases

### Problem
How do we ensure robustness under unusual conditions?

### Solution: Create minimal/maximal/empty test cases

```python
class TestEdgeCases:
    """Test edge cases that might break the system"""
    
    def test_empty_deck_zones(self):
        """Test creating zones with empty deck"""
        zones = PlayerZones(
            player_name='Player',
            deck=(),           # Empty tuple
            hand=(),           # Empty tuple
            discard=(),
            removed=()
        )
        
        assert len(zones.deck) == 0
        # Verify no crashes when accessing empty collections
        assert zones.total_cards() == 0
    
    def test_card_with_zero_cost(self):
        """Test card with zero cost (free cards)"""
        card = Card(code='free', name='Free Card')
        
        assert card.code == 'free'
        # Verify it doesn't break cost calculations
        assert isinstance(card.code, str)
    
    def test_deck_with_many_cards(self):
        """Test deck with maximum card count"""
        cards = (
            DeckCard(code='card1', quantity=100),  # Many copies
        )
        deck = Deck(id='test', name='Big Deck', cards=cards)
        
        assert deck.total_cards() == 100
        assert len(deck.cards) == 1
```

---

## Pattern 6: Testing Dependencies Between Components

### Problem
How do we test that components work together?

### Solution: Mock interface, verify integration

```python
def test_deck_interactor_with_card_interactor_dependency(self):
    """Test that DeckInteractor properly uses CardInteractor"""
    
    # Setup mocks for all dependencies
    mock_repo = Mock()
    mock_card_interactor = Mock(spec=CardInteractor)  # Spec ensures interface match
    mock_gateway = Mock()
    
    # Create the interactor with mocked dependencies
    deck_interactor = DeckInteractor(mock_repo, mock_card_interactor, mock_gateway)
    
    # Setup mock responses
    mock_gateway.get_deck_cards = Mock(return_value=[
        {'code': 'card1', 'quantity': 1},
        {'code': 'card2', 'quantity': 2}
    ])
    mock_card_interactor.import_cards_bulk = Mock()
    mock_repo.save = Mock(return_value=Deck(id='test', name='Test', cards=()))
    
    # Execute
    result = deck_interactor.import_deck_from_marvelcdb('deck123')
    
    # Verify the dependency was called correctly
    mock_card_interactor.import_cards_bulk.assert_called_once_with(['card1', 'card2'])
    assert result is not None
```

---

## Pattern 7: Fixtures for Reusable Setup

### Problem
We repeat the same setup code in many tests.

### Solution: Use pytest fixtures

```python
@pytest.fixture
def card_interactor():
    """Create a fresh CardInteractor with mocked dependencies for each test"""
    mock_repo = Mock()
    mock_gateway = Mock()
    mock_storage = Mock()
    return CardInteractor(mock_repo, mock_gateway, mock_storage)

@pytest.fixture
def sample_cards():
    """Create sample card entities"""
    return (
        Card(code='card1', name='Card 1'),
        Card(code='card2', name='Card 2'),
    )

# Usage in tests
def test_search_multiple_cards(self, card_interactor, sample_cards):
    """Fixture parameters are automatically injected"""
    card_interactor.card_repo.search_by_name = Mock(return_value=sample_cards)
    result = card_interactor.search_cards('Card')
    assert len(result) == 2
```

---

## Pattern 8: Parametrized Tests

### Problem
We want to test the same logic with different inputs.

### Solution: Use `@pytest.mark.parametrize`

```python
@pytest.mark.parametrize("deck_cards, expected_count", [
    ((), 0),
    ((DeckCard(code='c1', quantity=1),), 1),
    ((DeckCard(code='c1', quantity=3), DeckCard(code='c2', quantity=2)), 5),
])
def test_deck_total_cards(deck_cards, expected_count):
    """Test deck card counting with different inputs"""
    deck = Deck(id='test', name='Test', cards=deck_cards)
    assert deck.total_cards() == expected_count
```

---

## Best Practices

### ✅ DO
1. **Use meaningful test names** that describe what is being tested
   ```python
   def test_import_card_from_marvelcdb_when_not_exists()  # Good
   def test_import_card()  # Bad
   ```

2. **Arrange-Act-Assert pattern**
   ```python
   def test_something():
       # ARRANGE: Set up test data and mocks
       mock_repo = Mock()
       
       # ACT: Execute the code being tested
       result = function_under_test(mock_repo)
       
       # ASSERT: Verify the result
       assert result is not None
   ```

3. **Test one thing per test**
   ```python
   def test_import_card()  # Good: one behavior
   def test_import_card_and_save_image_and_update_db()  # Bad: too many
   ```

4. **Use fixtures for common setup**
   ```python
   @pytest.fixture
   def interactor():
       return CardInteractor(Mock(), Mock(), Mock())
   ```

5. **Mock external dependencies**
   ```python
   card_interactor.marvelcdb = Mock()  # Don't call real API
   ```

6. **Verify both success and error paths**
   ```python
   def test_success():
       result = function()
       assert result is not None
   
   def test_error():
       with pytest.raises(ValueError):
           function_that_errors()
   ```

### ❌ DON'T
1. **Don't test private methods** (methods starting with `_`)
   - Test the public interface instead
   - If you need to test private methods, consider making them public

2. **Don't leave tests in intermediate states**
   - Use fixtures to reset state for each test
   - Each test should be independent

3. **Don't have inter-test dependencies**
   ```python
   def test_a():
       # DON'T rely on test_b running first
       pass
   ```

4. **Don't use real external services** in unit tests
   - Mock MarvelCDB API calls
   - Mock database operations (use mongomock)
   - Mock file I/O

5. **Don't write tests that are hard to debug**
   - Make test names clear
   - Use assertions with messages: `assert x is not None, "x should not be None"`

---

## Running Tests Effectively

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_interactors_advanced.py -v
```

### Run specific test
```bash
pytest tests/test_interactors_advanced.py::TestCardInteractorAdvanced::test_import_card_from_marvelcdb_new -v
```

### Run with coverage
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Run and stop on first failure
```bash
pytest tests/ -x
```

### Run with detailed output
```bash
pytest tests/ -vv
```

---

## Coverage Goals

### Target Coverage Levels
| Layer | Target | Current |
|-------|--------|---------|
| Entities | 95%+ | 100% ✅ |
| Repositories | 90%+ | 83% 🟡 |
| Interactors | 85%+ | 73% 🟡 |
| Gateways | 70%+ | 55% 🟡 |
| Controllers | 80%+ | 0% ❌ |
| **Overall** | **70%+** | **35%** 🟡 |

### How to Improve Coverage
1. Run coverage report: `pytest --cov=src --cov-report=term-missing`
2. Identify uncovered lines (marked with "Missing")
3. Write tests for those lines
4. Re-run to verify improvement

---

## Common Testing Mistakes

### ❌ Mistake 1: Testing Implementation Instead of Behavior
```python
# Bad: Tests implementation details
def test_dict_has_key():
    result = function()
    assert 'id' in result  # Testing dict keys

# Good: Tests behavior
def test_returns_game_with_id():
    result = function()
    assert result.id is not None
```

### ❌ Mistake 2: Overly Complex Mocks
```python
# Bad: Mock setup is harder to understand than the code
mock = Mock()
mock.method1.return_value.method2.return_value = Mock()
mock.method1.return_value.method2.return_value.method3 = Mock()

# Good: Clear mock setup
mock = Mock()
mock.get_card_info.return_value = {'code': 'test', 'name': 'Test'}
```

### ❌ Mistake 3: Testing Too Many Things at Once
```python
# Bad: Test does everything
def test_game_flow():
    create_card()
    create_deck()
    create_game()
    draw_card()
    play_card()
    # If this fails, what broke?

# Good: Tests are focused
def test_create_game_with_deck()
def test_draw_card_updates_hand()
def test_play_card_validates_cost()
```

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

## Next Steps

1. Use these patterns for new tests
2. Apply to controller/API endpoint tests
3. Add integration tests for workflows
4. Aim for 70%+ coverage before production
