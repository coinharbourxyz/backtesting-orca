# Orca Koii Task for Backtesting CoinHarbour's Algo Trading Strategy

### Task Functions

Perform 4 functions:
1. Task
2. Submission
3. Audit
4. Distribute rewards

These four functions are defined in the file `src/index.js`.

In a regular Koii task, you would write your task logic here. In the case of an Orca task, three of these functions make calls to your HTTP endpoints within your container. In most cases, you will not need to edit these functions.

The fourth function, `distribution` defines your compensation logic, and can be edited as needed.

- `task(roundNumber)`: Makes a get request to the endpoint `/task/:roundNumber`.
- `submission(roundNumber)`: Makes a get request to the endpoint `/submission/:roundNumber`, then uploads the submission data to IPFS and returns the file CID to be submitted on chain as the submission proof.
- `audit(submission, roundNumber)`: Retrieves the submission data from IPFS using the CID that was submitted on chain. Makes a post request to `/audit` and returns the result.
- `distribution(submitters, bounty, roundNumber)`: The default code deducts 70% of the stake for nodes that fail audit and distributes the bounty for that round (defined by `bounty_per_round` in your `config-task.yml`) equally between all nodes that pass audit.

## Using Orca

The Orca task template is designed to simplify the steps needed for integration with Koii Tasks. To that end, there are only two main elements you need to configure:

1. Container creation
2. Task endpoints

### Container Creation

A sample container is provided in the `container` folder.

### Container Port

The container must listen on port 8080.


### Container Endpoints

Your container must have 4 HTTP endpoints:

- `/healthz`: To verify your container is running, Orca requires an endpoint at that accepts a post request and returns a 200 response. The content of the response is unimportant.
- `/task/:roundNumber`. This endpoint should kick off the task each round, and store the result of the task (your proofs) with the round number, so it can be retrieved by `submission`.
- `/submission/:roundNumber` Retrieves the stored submission data.
- `/audit`: Check the submission (using whatever method makes sense for your task) and return a boolean representing whether or not the submission was correct.
