# vim: ft=bash

_SSH_ENVIRONMENT="$HOME/.ssh/agent-environment"

_start_ssh_agent() {
    (umask 066; ssh-agent | grep -v ^echo >"$_SSH_ENVIRONMENT")
    . "$_SSH_ENVIRONMENT"
    ssh-add;
}

_is_ssh_agent_running() {
    if [ -z "$SSH_AGENT_PID" ]
    then
        return 1
    fi
    ps xa -o pid,command | grep -qE "^\s*$SSH_AGENT_PID ssh-agent$"
}

_auto_start_ssh_agent() {
    if [ -f "$_SSH_ENVIRONMENT" ]
    then
        . "$_SSH_ENVIRONMENT"
        if ! _is_ssh_agent_running
        then
            _start_ssh_agent
        fi
    else
        _start_ssh_agent;
    fi
}

_auto_start_ssh_agent
