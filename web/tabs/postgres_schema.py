"""PostgreSQL Schema Tab - Generate PostgreSQL schema from Airtable metadata"""
from pyscript import document, window
import sys
sys.path.append("web")
from components.airtable_client import get_local_storage_metadata
from components.error_handling import handle_tab_error, display_error_in_element, validate_metadata, AnalysisError
from postgres_schema_generator import (
    generate_schema,
    DATA_FIELD_TYPES,
    COMPUTED_FIELD_TYPES,
    ALL_FIELD_TYPES,
)


def initialize():
    """Initialize the PostgreSQL schema tab"""
    window.generatePostgresSchema = generate_postgres_schema
    print("PostgreSQL schema tab initialized")


def generate_postgres_schema():
    """Generate PostgreSQL schema from loaded Airtable metadata"""
    output_element = document.getElementById("postgres-schema-output")
    
    try:
        # Get and validate metadata
        metadata = validate_metadata(get_local_storage_metadata())
        
        # Get form values
        naming_mode = document.getElementById("postgres-naming-mode").value
        field_types_option = document.getElementById("postgres-field-types").value
        include_formulas = document.getElementById("postgres-include-formulas").checked
        
        # Determine which field types to include
        if field_types_option == "all":
            included_field_types = ALL_FIELD_TYPES
        elif field_types_option == "data":
            included_field_types = DATA_FIELD_TYPES
        elif field_types_option == "computed":
            included_field_types = COMPUTED_FIELD_TYPES
        elif field_types_option == "data+computed":
            included_field_types = DATA_FIELD_TYPES | COMPUTED_FIELD_TYPES
        else:
            included_field_types = None
        
        # Generate schema
        sql = generate_schema(
            metadata,
            naming_mode=naming_mode,
            included_field_types=included_field_types,
            include_formulas_as_generated=include_formulas,
            formula_max_depth=2
        )
        
        # Display result
        output_element.innerHTML = f"""
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md transition-colors duration-200">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Generated PostgreSQL Schema</h3>
                    <button onclick="copyPostgresSchema()" 
                            class="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2 px-4 rounded-lg shadow-sm hover:shadow transition-all duration-150">
                        Copy SQL
                    </button>
                </div>
                <pre class="bg-gray-50 dark:bg-gray-900 p-4 rounded overflow-x-auto text-sm"><code id="postgres-schema-code" class="text-gray-800 dark:text-gray-200">{sql}</code></pre>
            </div>
        """
        
    except AnalysisError as e:
        handle_tab_error(e, "generating PostgreSQL schema", "postgres-schema-output")
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        display_error_in_element(error_msg, "postgres-schema-output")
        print(f"Error in generate_postgres_schema: {e}")
        import traceback
        traceback.print_exc()


def copy_postgres_schema():
    """Copy the generated SQL to clipboard"""
    try:
        code_element = document.getElementById("postgres-schema-code")
        if code_element:
            sql_text = code_element.textContent
            window.navigator.clipboard.writeText(sql_text)
            
            # Show feedback
            print("SQL copied to clipboard")
            
    except Exception as e:
        print(f"Error copying SQL: {e}")


# Export copy function to window for onclick handler
window.copyPostgresSchema = copy_postgres_schema
