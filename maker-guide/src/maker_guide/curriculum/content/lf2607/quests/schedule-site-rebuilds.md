# Publish Singapore Conditions

Quest: schedule-site-rebuilds

## Mission

Complete the released Singapore Today shell starter's field extraction and Markdown composition, then publish validated forecast and modelled PM2.5 data as scheduled static content.

## Make It Yours

Follow [S9 self-study](../sessions/S09/self-study.md#challenge-publish-singapore-conditions) to copy the intentionally incomplete `singapore-today.sh` starter once, link `singapore-today.html` from the homepage, run it before the build, and schedule the build daily at 09:00. Personalize the presentation and keep source attribution, units, forecast date, air timestamp, and retrieval timestamp clear. PM2.5 is CAMS model data, not official PSI or a local-station reading.

## Check The Result

Run the service and inspect its journal. Confirm `/singapore-today.html` is linked and published. Use the provided validation and nonempty-output checks; prove a short timer activation publishes your personalized heading and a fresh retrieval timestamp. A timer listing is a planned deadline, not proof of a successful update. Restore the regular daily schedule after testing.
