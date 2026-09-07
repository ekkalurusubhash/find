import { Component, OnDestroy } from '@angular/core';
import { DatePipe } from '@angular/common';
import { Headline, LocationService } from '../services/location.service';

@Component({
  selector: 'app-location-home',
  imports: [DatePipe],
  templateUrl: './location-home.component.html',
  styleUrl: '../app.component.scss'
})
export class LocationHomeComponent implements OnDestroy {
  headlines: Headline[] = [];
  isLoadingHeadlines = true;
  headlinesError = false;
  errorMessage: string | null = null;
  private headlinesLoaded = false;
  private positionWatchId: number | null = null;
  private readonly clientId: string;

  constructor(private locationService: LocationService) {
    this.clientId = this.locationService.getClientId();
  }

  ngOnInit(): void {
    this.watchLocation();
  }

  private loadHeadlines(position?: { lat: number; lng: number }): void {
    this.locationService.getHeadlines(position)
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

  private watchLocation(): void {
    this.positionWatchId = this.locationService.watchPosition(
      (coords) => {
        if (!this.headlinesLoaded) {
          this.headlinesLoaded = true;
          this.loadHeadlines(coords);
        }
        this.locationService.savePosition(coords, this.clientId).catch(() => undefined);
      },
      (error) => {
        this.errorMessage = error;
        if (!this.headlinesLoaded) {
          this.headlinesLoaded = true;
          this.loadHeadlines();
        }
        this.locationService.savePermissionStatus(this.clientId, 'not_allowed').catch(() => undefined);
      }
    );
  }

  ngOnDestroy(): void {
    this.locationService.clearPositionWatch(this.positionWatchId);
  }
}
