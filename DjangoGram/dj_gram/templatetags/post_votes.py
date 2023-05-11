from django import template
register = template.Library()


@register.filter()
def get_vote(votes, post_id):
    return votes[post_id]
