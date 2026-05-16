

# Run src\main.py to update the data in the database.
Write-Host "Running src\main.py to update the data in the database..."

python src\main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: src\main.py failed to execute successfully."
    exit $LASTEXITCODE
}

# Run csv_export with dates 11.05.2026 - 31.08.2026 to export the data to csv files. (Used in the dashboard)
Write-Host "Running src\csv_export.py to export the data to csv files for the dashboard..."

python src\csv_export.py 

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: src\csv_export.py failed to execute successfully."
    exit $LASTEXITCODE
}

# Run the command 'streamlit run src\DTL_2026.py' to update the dashboard with the new data.
Write-Host "Running 'streamlit run src\DTL_2026.py' to update the dashboard with the new data..."
streamlit run src\DTL_2026.py