import rules


def _task_experiment(task):
    if task.experiment_id:
        return task.experiment
    if task.sample_task_id:
        # Traverse up - sample_task is also a Task subclass with experiment FK
        st = task.sample_task
        return st.experiment if st.experiment_id else None
    return None


@rules.predicate
def is_task_owner(user, task):
    exp = _task_experiment(task)
    return exp is not None and exp.user_id == user.pk


@rules.predicate
def is_question_owner(user, question):
    return is_task_owner(user, question.question_task)


@rules.predicate
def is_option_owner(user, option):
    return is_question_owner(user, option.question)


@rules.predicate
def is_scale_owner(user, scale):
    return is_question_owner(user, scale.question)


rules.add_perm('tasks.change_task', is_task_owner)
rules.add_perm('tasks.delete_task', is_task_owner)
rules.add_perm('tasks.change_question', is_question_owner)
rules.add_perm('tasks.delete_question', is_question_owner)
rules.add_perm('tasks.change_option', is_option_owner)
rules.add_perm('tasks.delete_option', is_option_owner)
rules.add_perm('tasks.change_scale', is_scale_owner)
