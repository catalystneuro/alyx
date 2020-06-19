import os
from django.test import TestCase
from django.conf import settings
import trimesh
from trimesh import proximity

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

class TrimeshTests(TestCase):

    def setUp(self):
        self.points = []
        self.points.append([-11.94740292,48.38954010,-11.44560031])
        self.points.append([-11.27603690,20.04604200,-15.71733967])
        self.points.append([-14.27461295,19.3080065,-15.78077115])
        self.points.append([-15.63325161,17.13712371,-16.08717454])
        self.points.append([-18.30306228,31.87039064,-13.83168016])
        self.points.append([-7.756794536,14.17983954,-15.11223127])
        self.points.append([-10.96164467,35.77455778,-11.81482932])
        self.points.append([-11.20774277,19.24326409,-14.29568241])
        self.points.append([-12.54907562,16.83131541,-14.63825683])
        self.points.append([-14.1133076,17.32027068,-14.54049386])
        self.points.append([-15.69742797,18.01132484,-14.41168204])
        self.points.append([-19.29116561,44.63364909,-10.35514834])
        self.points.append([-9.381153979,15.48697158,-13.34758377])
        self.points.append([-13.4294074,47.94845194,-8.405777794])
        self.points.append([-12.76324815,19.66934237,-12.6657651])
        self.points.append([-14.00668694,15.98972436,-13.19952144])
        self.points.append([-17.67707805,43.61401824,-8.99392391])

        spock_stl = os.path.join(TEST_DIR + '/files', 'Spock_HPC.stl')
        self.mesh = trimesh.load(spock_stl)
    
    def test_point_is_in_stl(self):
        distance = proximity.signed_distance(self.mesh, self.points)
        
        self.assertEquals(False, distance[0] > 0)
        self.assertEquals(True, distance[1] > 0)
        self.assertEquals(True, distance[2] > 0)
        self.assertEquals(False, distance[3] > 0)
        self.assertEquals(False, distance[4] > 0)
        self.assertEquals(False, distance[5] > 0)
        self.assertEquals(False, distance[6] > 0)
        self.assertEquals(True, distance[7] > 0)
        self.assertEquals(True, distance[8] > 0)
        self.assertEquals(True, distance[9] > 0)
        self.assertEquals(True, distance[10] > 0)
        self.assertEquals(False, distance[11] > 0)
        self.assertEquals(False, distance[12] > 0)
        self.assertEquals(False, distance[13] > 0)
        self.assertEquals(False, distance[14] > 0)
        self.assertEquals(True, distance[15] > 0)
        self.assertEquals(False, distance[16] > 0)
