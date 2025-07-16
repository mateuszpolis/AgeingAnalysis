from ageing_analysis.services.grid_visualization_service import GridVisualizationService


class TestGridVisualizationServiceResourceLoading:
    def test_load_mappings_from_package_resources(self):
        # Instantiate without a directory to use package resources
        service = GridVisualizationService(mappings_dir=None)
        mappings = service.get_available_mappings()
        # There should be at least one mapping (fta.csv, ftc.csv)
        assert len(mappings) >= 1
        mapping_names = [m["name"] for m in mappings]
        assert "fta" in mapping_names or "ftc" in mapping_names
        # Check that the mapping data is loaded
        for mapping in mappings:
            mapping_info = service.get_mapping(mapping["name"])
            assert mapping_info is not None
            assert "mapping" in mapping_info
            assert isinstance(mapping_info["mapping"], dict)
            # Should have at least one channel
            assert len(mapping_info["mapping"]) > 0

    def test_refresh_mappings(self):
        service = GridVisualizationService(mappings_dir=None)
        old_mappings = service.get_available_mappings()
        service.refresh_mappings()
        new_mappings = service.get_available_mappings()
        assert old_mappings == new_mappings
