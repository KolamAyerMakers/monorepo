#!py

def run():
    return __salt__['roles.include_roles_sls']('roles.{role}')
