# sxtSimpleRunner
A super-simple config driven ETL runner for Space and Time.  This isn't really designed to be emulated / runnable by many folks, rather a sample of a small process that SXTLabs actually uses in production (API message blaster aside).

To setup and start running on MacOS or Linux, simply:
`. ./setup.sh`

To run the actual script, you will need:
- [dotenv (.env)](https://docs.spaceandtime.io/docs/dotenv) file placed here: `./src/.env`
  - see `./.env_sample` file 
- Space and Time credentials
- API endpoint to distribute messages (we use zapier)
- biscuit if you want to UPDATE the central timestamp (optional)

