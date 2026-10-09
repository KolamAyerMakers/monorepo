# Schedule Hourly Site Rebuilds

Quest: schedule-site-rebuilds

## Mission

Run the Singapore generator before the site build and schedule the user service hourly with a randomized delay.

## Make It Yours

Follow [S9 self-study](../sessions/S09/self-study.md) for the completed report and site-link steps. Configure `ExecStartPre` before the installed build helper, keep the service working directory, and use `OnCalendar=hourly` with `RandomizedDelaySec=55min`. The timer configuration and next deadline do not prove that a service ran or published a page. Do not claim actual publication without inspecting the generated output and service journal.

## Check The Result

Inspect the unit files and timer listing. Treat these as configuration evidence only; an actual run and publication require separate observation.
