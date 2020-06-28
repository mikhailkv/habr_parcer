from tortoise import fields
from tortoise.models import Model


class Post(Model):
    id = fields.IntField(pk=True)
    title = fields.TextField()
    text = fields.TextField()
    url = fields.TextField()

    class Meta:
        table = "post"

    def __str__(self):
        return self.title
