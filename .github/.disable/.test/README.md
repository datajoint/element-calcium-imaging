For local testing using act, you need to create few things: 
- make a `.test/artifacts` dir for `act --artifact-server-path ./.test/artifacts/`
- make a `.test/.secrets` file similar as `.env` for `act --secret-file ./.test/.secrets`