"""
Test Accuracy Package
Contains accuracy tests for Text2SQL system (40% of testing grade)

Test Distribution:
- Simple queries: 5 questions (basic SELECT, WHERE)
- Intermediate queries: 10 questions (JOINs 2-3 tables, GROUP BY, aggregations)
- Complex queries: 5 questions (JOINs 4+ tables, subqueries, complex aggregations)

Total: 20 analytics questions covering all complexity levels

Accuracy Scoring Formula:
- Execution Success (20%): 1 if query executes without errors else 0
- Result Match (40%): 1 if results match expected output else 0
- Query Quality (40%): Average of quality metrics
  - uses_proper_joins: No cartesian products
  - has_necessary_where: Proper filtering
  - correct_group_by: Appropriate grouping
  - efficient_indexing: Uses indexes effectively
  - execution_time: < 1 second

Final Accuracy Score = (0.20 * execution_success) + (0.40 * result_match) + (0.40 * query_quality)
"""

__all__ = [
    'test_simple_queries',
    'test_intermediate_queries',
    'test_complex_queries'
]
