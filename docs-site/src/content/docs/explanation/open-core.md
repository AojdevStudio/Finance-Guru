---
title: "The open-core position"
description: "Why everything ships free under AGPL and how Finance Guru relates to Keepfolio."
sidebar:
  order: 2
---

Finance Guru is converting, in place, from one owner's private system into an installable open project. The decisions below were locked in the repository's planning issue and shape everything else on this site.

## Everything is open

All skills, agents, and the Python engine ship free under the existing AGPL-3.0 license. The commercial layer is convenience, never withheld features. AGPL already prevents proprietary forks, so there is no need to hold anything back.

## Finance Guru is the free, CLI-native experience

Finance Guru is the self-hosted product for people comfortable in a terminal. Keepfolio is the polished product for people who will not run one. The free plugin is the funnel toward that product, and the relationship is stated openly rather than hidden.

## CSV-first connectivity

The system works on day one with broker CSV exports. SnapTrade and SimpleFIN live sync stay in the project as documented bring-your-own-credentials options for power users. There is no paid-API wall in the first hour.

## Built for technical operators

The first user is a technical operator already running an agent harness. Onboarding may assume CLI comfort, uv, and API-key literacy. That assumption keeps the docs honest about prerequisites instead of hiding them.

## Where the transition stands

The privacy foundation is done. The scanner, the push gates, and the data-classification policy are in place. The configurable data root and the instance scaffold shipped, so private data lives outside the repository. Plugin packaging for Claude Code and Codex is planned and being built in a separate effort. It is not on the default branch, so treat any plugin-install instructions as planned rather than shipped. Repositioning of the README for installers follows the packaging work.

## Why this order

Privacy came first because a public repository that ever carried household data cannot be un-published. Only after the gates held could the data move out, and only after the data moved out could packaging make the repository installable for someone else.

_This page is built from the decisions recorded in repository issue #131._
