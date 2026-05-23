from services.pdf_parser import parse_bank_statement

# Replace with your actual PDF path
df, bank = parse_bank_statement("test_statement.pdf")

if df is not None:
    print(f"\nBank: {bank}")
    print(f"Total transactions: {len(df)}")
    print(f"Total Debit:  ₹{df['debit'].sum():,.2f}")
    print(f"Total Credit: ₹{df['credit'].sum():,.2f}")
    print("\nFirst 5 transactions:")
    print(df.head())
    
    # Save to CSV to inspect
    df.to_csv("parsed_output.csv", index=False)
    print("\nSaved to parsed_output.csv")
else:
    print(f"Failed: {bank}")