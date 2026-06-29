from django.db import models


class FilterInterface(models.Model):
    interface = models.ForeignKey("Interface", on_delete=models.CASCADE)
    filter = models.ForeignKey("Filter", on_delete=models.CASCADE)
    direction = models.CharField(max_length=50)
    policy_sequence = models.IntegerField()
    enable = models.BooleanField(default=True)

    def __str__(self):
        return f"FilterInterface(interface_id={self.interface_id}, filter_id={self.filter_id}, direction='{self.direction}', policy_sequence={self.policy_sequence}, enable={self.enable})"
