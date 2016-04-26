from django.db import models
import school.models
import user.models


class Group(models.Model):
    for_school = models.ForeignKey(school.models.School, null=True, blank=True, related_name='groups')

    owner = models.ForeignKey(user.models.User, related_name='owned_groups')

    short_name = models.CharField(max_length=100,
                                  help_text='Используется в урлах. Лучше обойтись латинскими буквами, цифрами и подчёркиванием')

    label = models.CharField(max_length=30, help_text='Покороче, используется на метках')

    description = models.TextField(help_text='Подлинее, подробное описание')

    @property
    def group_members(self):
        return list(GroupInGroupMembership.objects.filter(group=self))

    @property
    def user_members(self):
        return list(UserInGroupMembership.objects.filter(group=self))

    @property
    def child(self):
        return self.group_members + self.user_members

    # TODO: cache calculated members of group?
    @property
    def members(self):
        members = set()
        visited_groups = {self}
        queue = [self]
        for group in queue:
            members += group.user_members
            for child_group in group.group_members:
                if child_group not in visited_groups:
                    visited_groups.add(child_group)
                    queue.append(child_group)
        return list(members)


class GroupMembership(models.Model):
    group = models.ForeignKey(Group, related_name='+')

    class Meta:
        abstract = True


class GroupInGroupMembership(GroupMembership):
    member = models.ForeignKey(Group, related_name='member_in_groups')


class UserInGroupMembership(GroupMembership):
    member = models.ForeignKey(user.models.User, related_name='member_in_groups')
