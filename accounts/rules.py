import rules


@rules.predicate
def is_admin(user):
    return bool(user and user.is_authenticated and user.admin)


rules.add_rule('accounts.admin_access', is_admin)
rules.add_perm('accounts.admin_access', is_admin)
