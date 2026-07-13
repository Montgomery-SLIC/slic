import rules


@rules.predicate
def is_experiment_owner(user, experiment):
    return bool(experiment and experiment.user_id == user.pk)


rules.add_perm('experiments.view_experiment', is_experiment_owner)
rules.add_perm('experiments.change_experiment', is_experiment_owner)
rules.add_perm('experiments.delete_experiment', is_experiment_owner)
