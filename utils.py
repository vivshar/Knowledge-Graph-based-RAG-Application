class BaseLogger:
    def __init__(self) -> None:
        self.info = print

def create_vector_index(driver, dimension: int) -> None:
    index_query = "CALL db.index.vector.createNodeIndex('yelp', 'restaurant', 'embedding', $dimension, 'cosine')"
    try:
        driver.query(index_query, {"dimension": dimension})
    except:  # Already exists
        pass

def create_constraints(driver):
    driver.query(
        "CREATE CONSTRAINT review_unique IF NOT EXISTS FOR (r:review) REQUIRE (r.text) IS UNIQUE"
    )
    driver.query(
        "CREATE CONSTRAINT restaurant_name IF NOT EXISTS FOR (r:restaurant) REQUIRE (r.name) IS UNIQUE"
    )
    driver.query(
        "CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:city) REQUIRE (c.name) IS UNIQUE"
    )
    driver.query(
        "CREATE CONSTRAINT state_name IF NOT EXISTS FOR (s:state) REQUIRE (s.name) IS UNIQUE"
    )
