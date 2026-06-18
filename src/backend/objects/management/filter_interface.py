from django.db import models


class FilterInterface(models.Model):
    interface_id = models.ForeignKey("Interface", on_delete=models.CASCADE)
    filter_id = models.ForeignKey("Filter", on_delete=models.CASCADE)
    direction = models.CharField(max_length=50)
    sequence = models.IntegerField()

    def __str__(self):
        return f"FilterInterface(interface_id={self.interface_id}, filter_id={self.filter_id}, direction='{self.direction}', sequence={self.sequence})"


# class FilterInterface:
#     def __init__(self, interface_id: int, filter_id: int, direction: str, sequence):
#         self.interface_id = interface_id
#         self.filter_id = filter_id
#         self.direction = direction
#         self.sequence = sequence

#     def __str__(self):
#         return f"FilterInterface(interface_id={self.interface_id}, filter_id={self.filter_id}, direction='{self.direction}', sequence={self.sequence})"
