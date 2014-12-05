# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView

from ralph_assets.models_assets import DeviceInfo, Orientation, Rack
from ralph_assets.models_dc_assets import RackAccessory
from ralph_assets.views.base import ACLGateway


TYPE_EMPTY = 'empty'
TYPE_ACCESSORY = 'accessory'
TYPE_ASSET = 'asset'


class AssetInfoPerRackAPIView(ACLGateway, APIView):
    """
    Collect and return information for visualization of racks.
    """
    def get(self, request, rack_id, format=None):
        """
        Collecting asset and device_info information for given rack id.

        :param rack_id int: rack id
        :returns list: list of informations about assets
        """
        try:
            rack = Rack.objects.get(id=rack_id)
        except Rack.DoesNotExist:
            return Response({
                'message': _('Rack with id `{0}` does not exist'.format(
                    rack_id
                )),
            }, status=HTTP_404_NOT_FOUND)

        def get_empty_positions(max_height, devices):
            positions = []
            for item in devices:
                position = int(item['position'])
                if item['_type'] == TYPE_ACCESSORY:
                    height = 1
                if item['_type'] == TYPE_ASSET:
                    height = int(item['height'])
                positions.extend(range(position, position + height))

            return set(xrange(1, max_height + 1)) - set(positions)

        def get_data_by_side(rack, side):
            results = []
            for device in DeviceInfo.objects.filter(
                rack=rack,
                orientation=side,
            ).select_related(
                'asset__model',
            ):
                results.append({
                    '_type': TYPE_ASSET,
                    'asset_id': device.asset.id,
                    'model': device.asset.model.name,
                    'height': int(device.asset.model.height_of_device),
                    'barcode': device.asset.barcode,
                    'sn': device.asset.sn,
                    'url': device.asset.url,
                    'position': device.position,
                })
            for rack_accessory in RackAccessory.objects.filter(
                rack=rack,
                orientation=side,
            ):
                results.append({
                    '_type': TYPE_ACCESSORY,
                    'position': rack_accessory.position,
                    'remarks': rack_accessory.remarks,
                    'type': rack_accessory.accessory.name,
                })
            for empty_position in get_empty_positions(
                rack.max_u_height, results
            ):
                results.append({
                    '_type': TYPE_EMPTY,
                    'position': empty_position,
                })
            return results

        sides = [
            {
                "type": side.desc,
                "items": get_data_by_side(rack, side)
            }
            for side in [Orientation.front, Orientation.back]
        ]
        return Response({
            "name": rack.name,
            "max_u_height": rack.max_u_height,
            "sides": sides
        })
