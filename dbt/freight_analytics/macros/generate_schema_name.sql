{% macro generate_schema_name(custom_schema_name, node) -%}
    {# If we specify 'public', we want it to stay 'public' #}
    {%- if custom_schema_name == 'public' -%}
        public
    {%- elif custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}