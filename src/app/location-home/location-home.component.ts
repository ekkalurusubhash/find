import { Component } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { LocationService } from '../services/location.service';
import { LocationMapComponent } from '../location-map/location-map.component';

@Component({
  selector: 'app-location-home',
  imports: [DecimalPipe, LocationMapComponent],
  templateUrl: './location-home.component.html',
  styleUrl: '../app.component.scss'
})
export class LocationHomeComponent {
  latitude: number | null = null;
  longitude: number | null = null;
  errorMessage: string | null = null;
  isLoading = true;

  constructor(private locationService: LocationService) {}

  ngOnInit(): void {
    this.getCurrentLocation();
  }

  getCurrentLocation(): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.locationService.getPosition()
      .then((coords) => {
        this.latitude = coords.lat;
        this.longitude = coords.lng;
        return this.locationService.savePosition(coords).catch(() => undefined);
      })
      .catch((error) => {
        this.errorMessage = typeof error === 'string' ? error : 'Unable to access your location.';
      })
      .finally(() => {
        this.isLoading = false;
      });
  }
}
