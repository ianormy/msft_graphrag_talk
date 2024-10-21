
def get_multiple(entity_id_filter: str, 
                 limit_chunks: int = 3, 
                 limit_communities: int = 3,
                 limit_inside_relationships: int = 10,
                 limit_outside_relationships: int = 10):
    """Generate a SPARQL query that will be used for our question context
    
    :param entity_id_filter: SPARQL filter statement for the top Entity records
    :param limit_chunks: the number of Chunk records to use
    :param limit_communities: the number of Community records to use
    :param limit_inside_relationships: the number of inside relationships to use
    :param limit_outside_relationships: the number of outside relationships to use
    :return: SPARQL query to use to generate RDF triples that will be used for the question context
    """
    query = """
    PREFIX gr: <http://ormynet.com/ns/msft-graphrag#>

SELECT * WHERE
{ 
  {
    #-- Entities -->
    SELECT ?description
    WHERE
    {
        ?entity_uri a gr:Entity;
        gr:id ?id;
        gr:description ?entity_desc .
        BIND(REPLACE(?entity_desc, "\\r\\n", " ", "i") AS ?description)
    """
    query += entity_id_filter
    query += """
    }
  }
  UNION
  {
    #-- Chunks -->
    SELECT 
    ?chunkText 
    (COUNT(?entity_uri) AS ?freq)
    WHERE {
        ?chunk_uri gr:has_entity ?entity_uri;
        gr:text ?chunk_text .
        ?entity_uri a gr:Entity;
            gr:id ?id .
    """
    query += entity_id_filter
    query += """
        BIND(REPLACE(?chunk_text, "\\r\\n", " ") as ?chunkText)
    }
    GROUP BY ?chunk_uri ?chunkText
    ORDER BY DESC(?freq)
    """
    query += f" LIMIT {limit_chunks} "
    query += """
  }
  UNION
  {
    #-- Communities -->
    SELECT ?summary
    WHERE
    {
        ?community_uri a gr:Community;
          gr:rank ?rank;
          gr:weight ?weight;
          gr:summary ?community_summary .
        BIND(REPLACE(?community_summary, "\\r\\n", " ", "i") AS ?summary)
        ?entity_uri gr:in_community ?community_uri;
            gr:id ?id .
    """
    query += entity_id_filter
    query += """
    }
    GROUP BY ?rank ?weight ?community_uri ?summary
    ORDER BY DESC(?rank) DESC(?weight)
    """
    query += f" LIMIT {limit_communities} "
    query += """
  }
  UNION
  {
    #-- Outside Relationships -->
    SELECT ?description
    WHERE {
        ?related_to_uri a gr:related_to;
            gr:id ?related_id;
            gr:rank ?rank;
            gr:description ?desc;
            gr:weight ?weight .
        BIND(REPLACE(?desc, "\\r\\n", "") as ?description)
        ?entity_from_uri ?related_to_uri ?entity_to_uri .
        ?entity_from_uri gr:id ?entity_from_id .
        ?entity_to_uri gr:id ?id .
    """
    query += entity_id_filter
    query += """
    }
    ORDER BY DESC(?rank) DESC(?weight)
    """
    query += f" LIMIT {limit_inside_relationships} "  
    query += """
  }
  UNION
  {
    #-- Inside Relationships -->
        SELECT ?description
        WHERE {
            ?related_to_uri a gr:related_to;
                gr:id ?related_id;
                gr:rank ?rank;
                gr:description ?desc;
                gr:weight ?weight .
            BIND(REPLACE(?desc, "\\r\\n", "") as ?description)
            ?entity_from_uri ?related_to_uri ?entity_to_uri .
            ?entity_from_uri gr:id ?id .
            ?entity_to_uri gr:id ?entity_to_id .
    """
    query += entity_id_filter
    query += """
    }
    ORDER BY DESC(?rank) DESC(?weight)
    """
    query += f" LIMIT {limit_outside_relationships} "  
    query += """
  }
}
    """
    return query