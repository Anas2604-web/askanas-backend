# DevConnect

## One-line summary
A full MERN-stack developer networking platform — think a Tinder-style swipe/match system for developers to connect — with real-time chat, subscription payments, and email notifications, deployed live with real users.

## Problem / context
Built as a full-stack learning and portfolio project to demonstrate end-to-end MERN capability: not just CRUD, but auth, matchmaking logic, payments, real-time messaging, and production email delivery — the full slice of what a real social/networking SaaS needs.

## Architecture
Express.js backend on MongoDB with Mongoose schemas for users, connections/requests, and feed ranking. React frontend (separate `DevConnect-frontend` repo) with Redux for state management (`userSlice`, `feedSlice`, `connectionSlice`, `requestSlice`). JWT-based auth with protected public/private routing and persisted login on refresh. Real-time chat via Socket.io. Razorpay integration for premium subscriptions with webhook-based payment verification. AWS SES for transactional email (signup, password reset, cron-based scheduled reminders).

## Tech stack
MongoDB, Express.js, React.js, Node.js, Socket.io, Razorpay, AWS SES, Redux, AWS EC2, Nginx.

## Key decisions & why
- **Score-based matchmaking for feed ranking** — rather than a naive random or chronological feed, implemented a scoring approach to rank potential connections, closer to how a real networking/dating-style product would prioritize matches.
- **Compound indexing + schema-level validation on connections** — used compound indexes and `schema.pre` hooks for data integrity on the connection/request model, rather than relying purely on application-layer checks.
- **Rate limiting on sensitive routes** — added a "swipe limiter" middleware to rate-limit swipe/match actions, and rate limiting on edit-profile/edit-password endpoints, tested via Postman before shipping.
- **Webhook-based Razorpay verification** — built a dedicated webhook + verify route to confirm payment status from Razorpay reliably, rather than trusting client-side payment confirmation alone.
- **Cron-based email reminders wrapped in try/catch** — deliberately isolated email-sending failures so a broken email send couldn't break the main request flow — a small but real production-reliability decision.

## Challenges & fixes
- **CORS and origin issues in production** — fixed incorrect origin configuration that was causing production request failures, and separately ensured API URLs worked correctly in both local and production environments (multiple iterative fixes across several commits).
- **Auth persistence and protected routing** — implemented public/private protected routes with login state persisting correctly across page refreshes, rather than losing session state on reload.
- **JWT secret handling** — secured the JWT secret token (moved from a less safe initial setup to proper secret handling).
- **Iterative validation hardening** — fixed API bugs and validation issues, then followed up with further refinement of edit-profile field validation to only allow specific fields to be edited (not a full unrestricted update).
- **Real-time chat build** — implemented the chat component and underlying real-time messaging via Socket.io on top of the existing REST API and Redux state layers.

## Results / metrics
Deployed live with ~10 real users on AWS EC2 with Nginx. Full payment flow (order creation → webhook verification → premium feature unlock) working end-to-end with Razorpay in production, not just sandbox/test mode.

## Links
Backend: https://github.com/Anas2604-web/DevConnect
Frontend: https://github.com/Anas2604-web/DevConnect-frontend
Live: devconnectweb.xyz