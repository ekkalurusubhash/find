import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-location-map',
  templateUrl: './location-map.component.html',
  styleUrl: './location-map.component.scss'
})
export class LocationMapComponent {
  @Input({ required: true }) latitude!: number;
  @Input({ required: true }) longitude!: number;

  get mapUrl(): string {
    const padding = 0.01;
    const west = this.longitude - padding;
    const south = this.latitude - padding;
    const east = this.longitude + padding;
    const north = this.latitude + padding;

    return `https://www.openstreetmap.org/export/embed.html?bbox=${west}%2C${south}%2C${east}%2C${north}&layer=mapnik&marker=${this.latitude}%2C${this.longitude}`;
  }
}
