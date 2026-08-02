FROM opensearchproject/opensearch:2.18.0

# Install Kuromoji plugin
RUN /usr/share/opensearch/bin/opensearch-plugin install analysis-kuromoji

# Copy custom config
COPY docker/opensearch/opensearch.yml /usr/share/opensearch/config/opensearch.yml
