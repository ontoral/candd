Post Files
==========

1. Download TIAA-CREF files from the previous day
 a. Login to http://tiaa-cref.org
 b. Click "Client Data Download"
 c. Click "Download Current File"
 d. Expand files to "C:\portfoliocenter-data\tiaa-cref-exports\"
 e. Move current .zip file to "C:\portfolio-center-data\tiaa-cref-exports\archives\"
 f. Run TIAA-CREF converter program
2. Open and review Securities
 * Clean up names:
  - Remove rates/dates from title
  - Move any geographical location to comment
  - Expand common abbreviations
  - Lookup CUSIP for further info (http://fixedincome.fidelity.com, etc.)
3. Save any changes
4. Post Securities
5. Open and review Prices
 * Search for anomalies:
  - Sort by Status (look for Error)
  - Sort by Price High (verify indexes and other top performers)
  - Sort by Price Low (verify the usual zeroes, make sure no other securities are missing price)
  - Sort by Type (verify Indexes prices received from supplemental downloads)
6. Save any changes
7. Post Prices
8. Open and review Portfolios
 * Ignore all Update status portfolios
 * Post any Pending status (new account) portfolios
  - Open "Null Entry Prevention/New Accounts" view in Data Manager, and enter data
9. Save any changes
10. Post Portfolios (confirm update overwrite dialog that opens)
11. Confirm no Position files are listed
12. Open and review Transactions
 *Sort by Activity:
  - Block or confirm Journals
  - Confirm Receipt of Securities as new assets
  - Block Corporate Actions (CA): Splits, Mergers, ROP, Return...
  - Use Transaction Writer to write CA substitutes
  - Review and research any warnings or errors
13. Post Transactions
14. Open and run Share Reconciliation Report (Share Rec)
 * Use approprate date
 * Choose portfolio set: Reconcilers (Open Accounts, Customers, No External Holdings)
15. Resolve Quantity Difference issues

Clean Up Data
=============

1. Look in Securities
2. Look in Transaction Writer
