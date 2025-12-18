# Seed

This project is a proof-of-concept which aims to use the [CypherTap](https://github.com/cypherflow/cyphertap) Svelte component to create a nostr-native website that accepts [eCash](https://cashu.space) payments.  This application will be charge 2 sats for each use in a 20 question quiz of spelling words.

## Project Requirements

The following project requirements should be strictly followed:

 * **Documentation:** This project's documentation should be kept up-to-date with code changes. It should remain terse and to-the-point without listing verbose chronological changelogs. It will be hosted on Github Pages out of the `docs/` directory and use the MKDocs format.

 * **CypherTap:** This Svelte component runs entirely in the browser and handles nostr authentication and ecash management for users.

 * **User accounts:** This website is "nostr native" where each user is identified by their "npub" or public key. Users are responsible for their own key management and wallet management. The CypherTap component is client-side and enables users to "log in" as well as handle their ecash balance.

 * **Cashu Nutshell:** This project will use its own [Cashu hot wallet](https://github.com/cashubtc/nutshell) and will not run a lightning/bitcoin node to operate as a proper mint. Payments from the users will be redeemed immediately and withdrawn to a lightning address periodically, if over a threashold.

 * **Docker Compose:** This project will be deployed using Docker. The intent is for end-users to build from source, so we will not push an image to Docker Hub.

 * **Local Storage:** Instead of using Docker volumes we will ensure that all local databases are kept in a `volumes/` directory for easy accessibility, portability, backup and recovery. `.env` files are placed in this repo's root.

 * **Frontend:** This will be build using Svelte 5 + tailwindcss + Vite. It should be responsive and default to dark mode. The CypherTap's dark mode toggle should be used to change the app's appearance.

 * **Backend:** This will be built using Python 3.12+ and FastAPI.

 * **Pay-Per-Use:** Instead of subscriptions, users will pay for their usage using eCash tokens. These bearer assets will be sent along with API requests to the backend to be redeemed and verified before processing a user's request, returning an HTTP 402 error if verification fails.
