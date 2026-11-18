CREATE TABLE property_map(
    dataset_id TEXT NOT NULL REFERENCES datasets(id),
    raw_name TEXT NOT NULL,
    property_id TEXT NOT NULL,
    PRIMARY KEY(dataset_id, raw_name)
);
CREATE INDEX property_map_id ON property_map(property_id);

CREATE VIEW unified_sources AS
 SELECT s.*, s.id || '#sha256:' || s.sha256 AS source_version_id FROM sources s;

CREATE VIEW unified_materials AS
 SELECT m.*, CASE
     WHEN json_type(m.metadata_json,'$.entity_kind')='text' THEN json_extract(m.metadata_json,'$.entity_kind')
     WHEN m.kind='assembly' THEN 'assembly'
     WHEN m.dataset_id='wood' THEN 'wood_reference'
     WHEN m.dataset_id='technical' THEN 'simulation_input'
     WHEN m.kind='product' THEN 'product_reference'
     ELSE 'generic_reference' END AS entity_kind,
   'family:' || m.category AS family_id,
   CASE WHEN m.dataset_id='environmental' AND instr(m.id,'@') > 0
        THEN substr(m.id,1,instr(m.id,'@')-1) ELSE m.id END AS lineage_id,
   s.source_version_id, s.url AS source_url
 FROM materials m JOIN unified_sources s ON m.source_id=s.id;

CREATE VIEW unified_observations AS
 SELECT o.*, p.property_id,
   COALESCE(json_extract(o.metadata_json,'$.value_kind'),
     CASE WHEN o.value IS NULL THEN 'text' ELSE 'scalar' END) AS value_kind,
   json_extract(o.metadata_json,'$.structured_value') AS structured_value_json,
   s.source_version_id, s.url AS source_url, s.license_status
 FROM observations o JOIN property_map p ON p.dataset_id=o.dataset_id AND p.raw_name=o.property
 JOIN unified_sources s ON s.id=o.source_id;

-- Explicit links complement source-record identities. A family is a search group.
CREATE TABLE material_links(
    material_id TEXT NOT NULL REFERENCES materials(id),
    relation TEXT NOT NULL,
    target_id TEXT NOT NULL REFERENCES materials(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    source_locator TEXT NOT NULL,
    PRIMARY KEY(material_id,relation,target_id,source_id,source_locator)
);
CREATE INDEX material_links_target ON material_links(target_id);

CREATE TABLE material_citations(
    material_id TEXT NOT NULL REFERENCES materials(id),
    source_id TEXT NOT NULL REFERENCES sources(id),
    source_locator TEXT NOT NULL,
    cited_source_id TEXT NOT NULL REFERENCES sources(id),
    PRIMARY KEY(material_id, source_id, source_locator, cited_source_id)
);
