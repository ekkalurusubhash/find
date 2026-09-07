import { Component } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Headline, LocationService } from '../services/location.service';

@Component({
  selector: 'app-location-home',
  imports: [DatePipe],
  templateUrl: './location-home.component.html',
  styleUrl: '../app.component.scss'
})
export class LocationHomeComponent {
  headlines: Headline[] = [];
  isLoadingHeadlines = true;
  headlinesError = false;
  errorMessage: string | null = null;

  constructor(private locationService: LocationService) {}

  ngOnInit(): void {
    this.loadHeadlines();
    this.captureLocation();
  }

  private loadHeadlines(): void {
    this.locationService.getHeadlines()
      .then((headlines) => {
        this.headlines = headlines;
      })
      .catch(() => {
        this.headlinesError = true;
      })
      .finally(() => {
        this.isLoadingHeadlines = false;
      });
  }

  private captureLocation(): void {
    this.locationService.getPosition()
      .then((coords) => {
        return this.locationService.savePosition(coords).catch(() => undefined);
      })
      .catch((error) => {
        this.errorMessage = typeof error === 'string' ? error : 'Unable to access your location.';
      });
  }
}
