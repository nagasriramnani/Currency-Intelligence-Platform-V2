'use client';

import React from 'react';

export function CampingLoader() {
    return (
        <div className="camping-loader-wrapper">
            <div className="scene">
                <div className="forest">
                    <div className="tree tree1">
                        <div className="branch branch-top" />
                        <div className="branch branch-middle" />
                    </div>
                    <div className="tree tree2">
                        <div className="branch branch-top" />
                        <div className="branch branch-middle" />
                        <div className="branch branch-bottom" />
                    </div>
                    <div className="tree tree3">
                        <div className="branch branch-top" />
                        <div className="branch branch-middle" />
                        <div className="branch branch-bottom" />
                    </div>
                    <div className="tree tree4">
                        <div className="branch branch-top" />
                        <div className="branch branch-middle" />
                        <div className="branch branch-bottom" />
                    </div>
                    <div className="tree tree5">
                        <div className="branch branch-top" />
                        <div className="branch branch-middle" />
                        <div className="branch branch-bottom" />
                    </div>
                    <div className="tree tree6">
                        <div className="branch branch-top" />
                        <div className="branch branch-middle" />
                        <div className="branch branch-bottom" />
                    </div>
                    <div className="tree tree7">
                        <div className="branch branch-top" />
                        <div className="branch branch-middle" />
                        <div className="branch branch-bottom" />
                    </div>
                </div>
                <div className="tent">
                    <div className="roof" />
                    <div className="roof-border-left">
                        <div className="roof-border roof-border1" />
                        <div className="roof-border roof-border2" />
                        <div className="roof-border roof-border3" />
                    </div>
                    <div className="entrance">
                        <div className="door left-door">
                            <div className="left-door-inner" />
                        </div>
                        <div className="door right-door">
                            <div className="right-door-inner" />
                        </div>
                    </div>
                </div>
                <div className="floor">
                    <div className="ground ground1" />
                    <div className="ground ground2" />
                </div>
                <div className="fireplace">
                    <div className="support" />
                    <div className="support" />
                    <div className="bar" />
                    <div className="hanger" />
                    <div className="smoke" />
                    <div className="pan" />
                    <div className="fire">
                        <div className="line line1">
                            <div className="particle particle1" />
                            <div className="particle particle2" />
                            <div className="particle particle3" />
                            <div className="particle particle4" />
                        </div>
                        <div className="line line2">
                            <div className="particle particle1" />
                            <div className="particle particle2" />
                            <div className="particle particle3" />
                            <div className="particle particle4" />
                        </div>
                        <div className="line line3">
                            <div className="particle particle1" />
                            <div className="particle particle2" />
                            <div className="particle particle3" />
                            <div className="particle particle4" />
                        </div>
                    </div>
                </div>
                <div className="time-wrapper">
                    <div className="time">
                        <div className="day" />
                        <div className="night">
                            <div className="moon" />
                            <div className="star star1 star-big" />
                            <div className="star star2 star-big" />
                            <div className="star star3 star-big" />
                            <div className="star star4" />
                            <div className="star star5" />
                            <div className="star star6" />
                            <div className="star star7" />
                        </div>
                    </div>
                </div>
            </div>
            <p className="loading-text">Loading Currency Intelligence...</p>
        </div>
    );
}
